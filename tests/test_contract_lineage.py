from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "check_contract_lineage.py"
SPEC = importlib.util.spec_from_file_location("contract_lineage", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
LINEAGE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = LINEAGE
SPEC.loader.exec_module(LINEAGE)


class ContractLineageTests(unittest.TestCase):
    def write(self, root: Path, name: str, text: str) -> None:
        (root / name).write_text(text, encoding="utf-8")

    def evaluate(self, root: Path, base_status: str = "PASS"):
        def fake_git(_root: Path, base: str):
            return (
                base_status,
                "abc123" if base_status == "PASS" else None,
            )

        return LINEAGE.evaluate(
            root,
            spec_path=Path("SPEC.md"),
            plan_path=Path("PLAN.md"),
            verify_path=Path("VERIFY.md"),
            handoff_path=Path("HANDOFF.md"),
            git_checker=fake_git,
        )

    def test_absent_identity_is_valid_and_inactive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(
                root,
                "SPEC.md",
                "# Spec\n\n## Objective\n- fix it\n",
            )
            self.write(root, "VERIFY.md", "# Verify\n")
            result = self.evaluate(root)

        self.assertEqual(result.status, "PASS")
        self.assertFalse(result.active)

    def test_active_contract_can_pass_across_existing_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(
                root,
                "SPEC.md",
                "Contract ID: task-2 | Parent: task-1 | Base commit: abc123\n"
                "Replan reason: compatibility seam\n",
            )
            self.write(root, "PLAN.md", "Contract ID: task-2\n")
            self.write(root, "VERIFY.md", "Contract ID: task-2\n")
            self.write(root, "HANDOFF.md", "Contract ID: task-2\n")
            result = self.evaluate(root)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(result.active_contract_id, "task-2")
        self.assertEqual(result.parent_contract_id, "task-1")

    def test_existing_downstream_artifact_missing_id_requires_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(
                root,
                "SPEC.md",
                "Contract ID: task-1 | Parent: none | Base commit: abc123\n"
                "Replan reason: none\n",
            )
            self.write(root, "VERIFY.md", "# Verify\n")
            result = self.evaluate(root)

        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertIn(
            "VERIFY exists but does not carry active Contract ID task-1",
            result.review_required,
        )

    def test_mismatched_downstream_id_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(
                root,
                "SPEC.md",
                "Contract ID: task-2 | Parent: none | Base commit: abc123\n"
                "Replan reason: none\n",
            )
            self.write(root, "VERIFY.md", "Contract ID: task-other\n")
            result = self.evaluate(root)

        self.assertEqual(result.status, "FAIL")
        self.assertIn(
            "VERIFY contract ID task-other does not match active contract task-2",
            result.failures,
        )

    def test_parent_contract_in_downstream_is_classified_obsolete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(
                root,
                "SPEC.md",
                "Contract ID: task-2 | Parent: task-1 | Base commit: abc123\n"
                "Replan reason: new scope\n",
            )
            self.write(root, "HANDOFF.md", "Contract ID: task-1\n")
            result = self.evaluate(root)

        self.assertEqual(result.status, "FAIL")
        self.assertIn(
            "HANDOFF references parent/obsolete contract task-1; "
            "active contract is task-2",
            result.failures,
        )

    def test_downstream_identity_without_spec_identity_requires_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(root, "SPEC.md", "# Spec\n")
            self.write(root, "VERIFY.md", "Contract ID: task-1\n")
            result = self.evaluate(root)

        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertFalse(result.active)

    def test_contract_cannot_parent_itself(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(
                root,
                "SPEC.md",
                "Contract ID: task-1 | Parent contract ID: task-1 | "
                "Base commit: abc123\nReplan reason: changed scope\n",
            )
            result = self.evaluate(root)

        self.assertEqual(result.status, "FAIL")
        self.assertIn(
            "active Contract ID cannot be its own parent",
            result.failures,
        )

    def test_parent_requires_replan_reason(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(
                root,
                "SPEC.md",
                "Contract ID: task-2 | Parent: task-1 | Base commit: abc123\n"
                "Replan reason: none\n",
            )
            result = self.evaluate(root)

        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertIn(
            "replanned contract has a parent but no meaningful Replan reason",
            result.review_required,
        )

    def test_unknown_base_requires_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(
                root,
                "SPEC.md",
                "Contract ID: task-1 | Parent: none | Base commit: unknown\n"
                "Replan reason: none\n",
            )
            result = self.evaluate(root)

        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertIn(
            "active contract Base commit is unknown",
            result.review_required,
        )

    def test_unestablished_base_requires_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(
                root,
                "SPEC.md",
                "Contract ID: task-1 | Parent: none | Base commit: deadbeef\n"
                "Replan reason: none\n",
            )
            result = self.evaluate(root, base_status="REVIEW_REQUIRED")

        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertIn(
            "Base commit could not be established as an ancestor of HEAD: deadbeef",
            result.review_required,
        )

    def test_multiple_ids_in_one_artifact_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(
                root,
                "SPEC.md",
                "Contract ID: task-1 | Parent: none | Base commit: abc123\n"
                "Replan reason: none\n",
            )
            self.write(
                root,
                "VERIFY.md",
                "Contract ID: task-1\nContract ID: task-2\n",
            )
            result = self.evaluate(root)

        self.assertEqual(result.status, "FAIL")
        self.assertIn(
            "VERIFY declares multiple contract IDs: task-1, task-2",
            result.failures,
        )

    def test_supersedes_alias_is_treated_as_parent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(
                root,
                "SPEC.md",
                "Contract ID: task-2\n"
                "Supersedes contract ID: task-1\n"
                "Base commit: abc123\n"
                "Replan reason: changed acceptance criterion\n",
            )
            result = self.evaluate(root)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(result.parent_contract_id, "task-1")

    def test_json_output_is_machine_readable(self) -> None:
        result = LINEAGE.Result(
            "PASS",
            False,
            None,
            None,
            None,
            (),
            (),
            (),
        )
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            LINEAGE.emit_json(result)

        payload = json.loads(output.getvalue())
        self.assertEqual(payload["status"], "PASS")
        self.assertFalse(payload["active"])


if __name__ == "__main__":
    unittest.main()
