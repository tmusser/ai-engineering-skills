from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_decision_ledger.py"
SPEC = importlib.util.spec_from_file_location("decision_ledger", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
LEDGER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = LEDGER
SPEC.loader.exec_module(LEDGER)


def entry(
    number: int, *, status: str = "ACTIVE", supersedes: str = "none",
    authority: str = "SPEC.md: accepted compatibility contract",
    when: str = "2026-11-14",
    extra: str = "",
) -> str:
    return (
        f"## D{number}: Preserve the existing export columns\n\n"
        f"- Status: {status}\n"
        f"- Date: {when}\n"
        f"- Authority: {authority}\n"
        "- Why: Existing clients depend on column order.\n"
        "- Alternatives: Reorder columns; rejected to preserve compatibility.\n"
        "- Evidence: src/export.py and tests/test_export.py.\n"
        "- Consequences: Keep header order fixed.\n"
        "- Revisit if: Downstream consumers approve a schema migration.\n"
        f"- Supersedes: {supersedes}\n"
        + extra + "\n"
    )


class DecisionLedgerTests(unittest.TestCase):
    def test_missing_or_bare_ledger_is_optional(self) -> None:
        self.assertEqual(LEDGER.evaluate(None).status, "NOT_APPLICABLE")
        self.assertEqual(LEDGER.evaluate("# Decisions\n\nNo durable decisions yet.\n").status,
                         "NOT_APPLICABLE")

    def test_valid_single_decision_passes(self) -> None:
        result = LEDGER.evaluate("# Decisions\n\n" + entry(1))
        self.assertEqual(result.status, "PASS", result.review_required)
        self.assertEqual(result.decisions[0]["id"], "D1")
        self.assertEqual(result.decisions[0]["status"], "ACTIVE")

    def test_valid_successor_requires_old_entry_to_be_marked_superseded(self) -> None:
        text = (
            "# Decisions\n\n"
            + entry(1, status="SUPERSEDED", when="2026-11-10")
            + entry(2, supersedes="D1")
        )
        result = LEDGER.evaluate(text)
        self.assertEqual(result.status, "PASS", result.review_required)
        self.assertEqual(result.decisions[1]["supersedes"], "D1")

    def test_active_predecessor_cannot_have_successor(self) -> None:
        result = LEDGER.evaluate("# Decisions\n\n" + entry(1) + entry(2, supersedes="D1"))
        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertIn("ACTIVE but superseded", str(result.review_required))

    def test_superseded_without_successor_is_incomplete(self) -> None:
        result = LEDGER.evaluate("# Decisions\n\n" + entry(1, status="SUPERSEDED"))
        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertIn("exactly one later successor", str(result.review_required))

    def test_missing_or_forward_or_self_supersedes_cannot_pass(self) -> None:
        for predecessor in ("D9", "D1", "", "D-1"):
            with self.subTest(predecessor=predecessor):
                result = LEDGER.evaluate("# Decisions\n\n" + entry(1, supersedes=predecessor))
                self.assertEqual(result.status, "REVIEW_REQUIRED")

    def test_multiple_successors_to_one_old_decision_requires_review(self) -> None:
        text = (
            "# Decisions\n\n"
            + entry(1, status="SUPERSEDED", when="2026-11-10")
            + entry(2, supersedes="D1")
            + entry(3, supersedes="D1")
        )
        result = LEDGER.evaluate(text)
        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertIn("multiple successors", str(result.review_required))

    def test_duplicate_ids_require_review(self) -> None:
        result = LEDGER.evaluate("# Decisions\n\n" + entry(1) + entry(1))
        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertIn("duplicate decision ID", str(result.review_required))

    def test_missing_rationale_and_authority_and_placeholders_require_review(self) -> None:
        sample = entry(1)
        for altered in (
            sample.replace("- Authority: SPEC.md: accepted compatibility contract\n", ""),
            sample.replace("- Why: Existing clients depend on column order.", "- Why: _TBD_"),
            sample.replace("- Evidence: src/export.py and tests/test_export.py.", "- Evidence: unknown"),
            sample.replace("- Revisit if: Downstream consumers approve a schema migration.", "- Revisit if:"),
        ):
            with self.subTest(altered=altered[:90]):
                result = LEDGER.evaluate("# Decisions\n\n" + altered)
                self.assertEqual(result.status, "REVIEW_REQUIRED")

    def test_invalid_status_date_and_predecessor_time_require_review(self) -> None:
        for sample in (
            entry(1, status="DRAFT"),
            entry(1, when="2026-02-30"),
            entry(1, when="yesterday"),
            entry(1, status="SUPERSEDED", when="2026-11-14")
            + entry(2, supersedes="D1", when="2026-11-01"),
        ):
            with self.subTest(sample=sample[:80]):
                result = LEDGER.evaluate("# Decisions\n\n" + sample)
                self.assertEqual(result.status, "REVIEW_REQUIRED")

    def test_unknown_or_repeated_fields_cannot_be_silent(self) -> None:
        for sample in (
            entry(1, extra="- Secret status: APPROVED\n"),
            entry(1, extra="- Authority: newly granted by the agent\n"),
            entry(1, extra="changed the decision without preserving rationale\n"),
        ):
            with self.subTest(sample=sample[-100:]):
                result = LEDGER.evaluate("# Decisions\n\n" + sample)
                self.assertEqual(result.status, "REVIEW_REQUIRED")

    def test_old_unstructured_ledger_receives_review_not_pass(self) -> None:
        result = LEDGER.evaluate(
            "# Decisions\n\n## Decision\n\n- Why: yes\n"
            "- Alternatives rejected: none\n- Date: today\n"
        )
        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertIn("heading must use", str(result.review_required))

    def test_fenced_examples_and_comments_do_not_create_decisions(self) -> None:
        fences = chr(96) * 3
        text = (
            "# Decisions\n\n"
            "~~~markdown\n" + entry(1) + "~~~\n\n"
            "<!--\n" + entry(9) + "-->\n\n"
            + fences + "markdown\n" + entry(2) + fences + "\n"
        )
        self.assertEqual(LEDGER.evaluate(text).status, "NOT_APPLICABLE")

    def test_cli_json_and_exit_codes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "DECISIONS.md"
            def run():
                return subprocess.run(
                    [sys.executable, str(SCRIPT), "--decisions", str(path),
                     "--format", "json"],
                    text=True, capture_output=True, check=False,
                )
            missing = run()
            self.assertEqual(missing.returncode, 0)
            self.assertEqual(json.loads(missing.stdout)["status"], "NOT_APPLICABLE")
            path.write_text("# Decisions\n\n" + entry(1), encoding="utf-8")
            valid = run()
            self.assertEqual(valid.returncode, 0)
            self.assertEqual(json.loads(valid.stdout)["status"], "PASS")
            path.write_text("# Decisions\n\n" + entry(1, status="SUPERSEDED"), encoding="utf-8")
            invalid = run()
            self.assertEqual(invalid.returncode, 3)
            self.assertEqual(json.loads(invalid.stdout)["status"], "REVIEW_REQUIRED")

    def test_directory_as_ledger_is_input_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            proc = subprocess.run(
                [sys.executable, str(SCRIPT), "--decisions", directory],
                text=True, capture_output=True, check=False,
            )
            self.assertEqual(proc.returncode, 2)
            self.assertIn("not a regular file", proc.stderr)


if __name__ == "__main__":
    unittest.main()
