from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "workflow_doctor.py"
SPEC = importlib.util.spec_from_file_location("workflow_doctor", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
DOCTOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = DOCTOR
SPEC.loader.exec_module(DOCTOR)

SPEC_READY = """# Spec

## Objective

Add a bounded export path.

## Acceptance criteria

- Export returns canonical rows.
"""
VERIFY_PASS = """# Verify

## Verify gate

Status: PASS

## Verification

- Remaining unverified risks: none
"""
VERIFY_FAIL = VERIFY_PASS.replace("Status: PASS", "Status: FAIL")
SCOPE_READY = """SCOPE FREEZE
Task: add export path
Allowed writes: export.py, tests/test_export.py
Read-only: schema.py
Forbidden: dependencies
Allowed commands: python -m unittest
Stop when: target tests pass
Invalid if: output schema changes
"""
HANDOFF = """# Handoff

## Next recommended task

- Add the CLI wrapper.
"""


def gate(status: str, *details: str, changed: tuple[str, ...] = ()):
    def run(root: Path, base: str | None, spec: Path, verify: Path):
        return DOCTOR.RuntimeResult(status, details or ("gate result",), changed)

    return run


def handoff(status: str, *details: str):
    def run(root: Path, path: Path):
        return DOCTOR.RuntimeResult(status, details or ("handoff result",))

    return run


class WorkflowDoctorTests(unittest.TestCase):
    def make_repo(self) -> Path:
        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        root = Path(tempdir.name)
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=root,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=root,
            check=True,
        )
        (root / "README.md").write_text("demo\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=root, check=True)
        subprocess.run(["git", "commit", "-qm", "initial"], cwd=root, check=True)
        return root

    def diagnose(
        self,
        root: Path,
        *,
        gate_status: str = "PASS",
        handoff_status: str = "NOT_PRESENT",
    ):
        return DOCTOR.diagnose(
            root,
            base="HEAD",
            verify_runner=gate(gate_status),
            handoff_runner=handoff(handoff_status),
        )

    def test_missing_spec_is_review_required(self) -> None:
        root = self.make_repo()
        (root / "VERIFY.md").write_text(VERIFY_PASS, encoding="utf-8")
        result = self.diagnose(root)
        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertIn("Create SPEC.md", result.next_move)

    def test_missing_artifacts_skip_the_verify_gate(self) -> None:
        root = self.make_repo()

        def must_not_run(root: Path, base: str | None, spec: Path, verify: Path):
            raise AssertionError("verify gate should not run")

        result = DOCTOR.diagnose(
            root,
            base="HEAD",
            verify_runner=must_not_run,
            handoff_runner=handoff("NOT_PRESENT"),
        )
        self.assertEqual(result.status, "REVIEW_REQUIRED")
        gate_check = next(
            check for check in result.checks if check.name == "VERIFY_GATE"
        )
        self.assertIn("required artifacts are incomplete", gate_check.details[0])

    def test_incomplete_optional_scope_blocks_more_changes(self) -> None:
        root = self.make_repo()
        (root / "SPEC.md").write_text(SPEC_READY, encoding="utf-8")
        (root / "VERIFY.md").write_text(VERIFY_PASS, encoding="utf-8")
        (root / "SCOPE.md").write_text(
            "SCOPE FREEZE\nTask: export\n",
            encoding="utf-8",
        )
        result = self.diagnose(root)
        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertIn("Reconcile the existing scope freeze", result.next_move)

    def test_absent_optional_scope_does_not_downgrade_green_evidence(self) -> None:
        root = self.make_repo()
        (root / "SPEC.md").write_text(SPEC_READY, encoding="utf-8")
        (root / "VERIFY.md").write_text(VERIFY_PASS, encoding="utf-8")
        result = self.diagnose(root)
        self.assertEqual(result.status, "PASS")
        scope = next(check for check in result.checks if check.name == "SCOPE")
        self.assertEqual(scope.status, "NOT_PRESENT")

    def test_scope_allows_explicit_none_for_forbidden_operations(self) -> None:
        text = SCOPE_READY.replace("Forbidden: dependencies", "Forbidden: none")
        result = DOCTOR.inspect_scope(text)
        self.assertEqual(result.status, "READY")

    def test_verify_failure_outranks_completion_claims(self) -> None:
        root = self.make_repo()
        (root / "SPEC.md").write_text(SPEC_READY, encoding="utf-8")
        (root / "SCOPE.md").write_text(SCOPE_READY, encoding="utf-8")
        (root / "VERIFY.md").write_text(VERIFY_FAIL, encoding="utf-8")
        result = self.diagnose(root, gate_status="PASS")
        self.assertEqual(result.status, "FAIL")
        self.assertIn("Fix the failing contract", result.next_move)

    def test_recorded_pass_without_deterministic_pass_is_not_upgraded(self) -> None:
        root = self.make_repo()
        (root / "SPEC.md").write_text(SPEC_READY, encoding="utf-8")
        (root / "VERIFY.md").write_text(VERIFY_PASS, encoding="utf-8")
        result = self.diagnose(root, gate_status="REVIEW_REQUIRED")
        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertIn("deterministic verify gate", result.next_move)

    def test_stale_handoff_suppresses_its_next_task(self) -> None:
        root = self.make_repo()
        (root / "SPEC.md").write_text(SPEC_READY, encoding="utf-8")
        (root / "VERIFY.md").write_text(VERIFY_PASS, encoding="utf-8")
        (root / "HANDOFF.md").write_text(HANDOFF, encoding="utf-8")
        result = self.diagnose(root, handoff_status="STALE")
        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertIsNone(result.trusted_next_task)
        self.assertNotIn("CLI wrapper", result.next_move)
        self.assertIn("regenerate HANDOFF.md", result.next_move)

    def test_fresh_handoff_can_supply_the_next_task(self) -> None:
        root = self.make_repo()
        (root / "SPEC.md").write_text(SPEC_READY, encoding="utf-8")
        (root / "VERIFY.md").write_text(VERIFY_PASS, encoding="utf-8")
        (root / "HANDOFF.md").write_text(HANDOFF, encoding="utf-8")
        result = self.diagnose(root, handoff_status="PASS")
        self.assertEqual(result.status, "PASS")
        self.assertEqual(result.trusted_next_task, "Add the CLI wrapper.")
        self.assertIn("Add the CLI wrapper", result.next_move)

    def test_diagnosis_is_read_only(self) -> None:
        root = self.make_repo()
        (root / "SPEC.md").write_text(SPEC_READY, encoding="utf-8")
        (root / "VERIFY.md").write_text(VERIFY_PASS, encoding="utf-8")
        before = {
            path.name: path.read_bytes()
            for path in root.iterdir()
            if path.is_file()
        }
        result = self.diagnose(root)
        after = {
            path.name: path.read_bytes()
            for path in root.iterdir()
            if path.is_file()
        }
        self.assertEqual(result.status, "PASS")
        self.assertEqual(before, after)

    def test_changed_files_are_forwarded_from_verify_gate(self) -> None:
        root = self.make_repo()
        (root / "SPEC.md").write_text(SPEC_READY, encoding="utf-8")
        (root / "VERIFY.md").write_text(VERIFY_PASS, encoding="utf-8")
        result = DOCTOR.diagnose(
            root,
            base="HEAD",
            verify_runner=gate(
                "PASS",
                changed=("export.py", "tests/test_export.py"),
            ),
            handoff_runner=handoff("NOT_PRESENT"),
        )
        self.assertEqual(
            result.changed_files,
            ("export.py", "tests/test_export.py"),
        )


if __name__ == "__main__":
    unittest.main()
