from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "acceptance_coverage.py"
RENDER_PATH = ROOT / "scripts" / "render_pr_evidence.py"

SPEC = importlib.util.spec_from_file_location("acceptance_coverage", PATH)
assert SPEC is not None and SPEC.loader is not None
COVERAGE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = COVERAGE
SPEC.loader.exec_module(COVERAGE)

RENDER_SPEC = importlib.util.spec_from_file_location("render_coverage", RENDER_PATH)
assert RENDER_SPEC is not None and RENDER_SPEC.loader is not None
RENDERER = importlib.util.module_from_spec(RENDER_SPEC)
sys.modules[RENDER_SPEC.name] = RENDERER
RENDER_SPEC.loader.exec_module(RENDERER)

SPEC_TEXT = """# Spec

## Acceptance criteria

- AC-1: CSV export preserves original columns.
- AC-2: Empty result is header-only.
- AC-3: Filter excludes unrelated rows.

## Non-goals

- No migration.
"""


def evidence(*rows: dict) -> str:
    fence = chr(96) * 3
    data = json.dumps({"schema_version": 1, "checks": list(rows)})
    return f"# Verify\n\n## Verify gate\n\nStatus: PASS\n\n## Structured verification evidence\n\n{fence}json\n{data}\n{fence}\n"


def check(name: str, criterion: str, *, status: str = "PASS",
          source: str = "command") -> dict:
    return {
        "check": name,
        "command": "pytest tests/test_export.py" if source == "command" else None,
        "exit_code": 0 if source == "command" else None,
        "evidence_source": source,
        "status": status,
        "evidence": "selected test produced the expected result",
        "recorded_at": "2026-10-27T12:00:00Z",
        "acceptance_criterion": criterion,
    }


class AcceptanceCoverageTests(unittest.TestCase):
    def test_complete_mapping_links_all_ids(self) -> None:
        result = COVERAGE.evaluate(
            SPEC_TEXT, evidence(check("export", "AC-1"), check("empty", "AC-2"), check("filter", "AC-3"))
        )
        self.assertTrue(result.active)
        self.assertEqual(result.status, "PASS")
        self.assertEqual([row.status for row in result.rows], ["LINKED"] * 3)

    def test_missing_criterion_downgrades_even_if_other_tests_pass(self) -> None:
        verify = evidence(check("export", "AC-1"), check("filter", "AC-3"))
        result = COVERAGE.evaluate(SPEC_TEXT, verify)
        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertEqual(result.rows[1].status, "MISSING")
        self.assertFalse(result.rows[1].checks)
        markdown = RENDERER.render_markdown(
            RENDERER.Artifact(Path("SPEC.md"), SPEC_TEXT),
            RENDERER.Artifact(Path("VERIFY.md"), verify),
            RENDERER.Artifact(Path("HANDOFF.md"), None),
            RENDERER.RuntimeCheck("PASS", []), None, "main",
        )
        self.assertIn("Overall: **REVIEW_REQUIRED**", markdown)
        self.assertIn("Acceptance coverage: **REVIEW_REQUIRED**", markdown)
        self.assertIn("| AC-2 | Empty result is header-only. | None | MISSING |", markdown)

    def test_missing_or_invalid_structured_evidence_cannot_fall_back_to_prose(self) -> None:
        for verify in (
            "# Verify\n## Command evidence\n- Acceptance criterion covered: AC-1\n",
            evidence(check("test", "AC-1")).replace('"schema_version": 1', '"schema_version": 2'),
        ):
            with self.subTest(verify=verify[:80]):
                result = COVERAGE.evaluate(SPEC_TEXT, verify)
                self.assertEqual(result.status, "REVIEW_REQUIRED")
                self.assertTrue(result.warnings)

    def test_failed_and_inferred_records_are_not_green(self) -> None:
        rows = (check("unit-tests", "AC-1", status="FAIL"),
                check("inference", "AC-2", source="inferred"),
                check("filter", "AC-3"))
        result = COVERAGE.evaluate(SPEC_TEXT, evidence(*rows))
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.rows[0].status, "FAIL")
        self.assertEqual(result.rows[1].status, "REVIEW_REQUIRED")

    def test_unknown_or_prose_reference_requires_review(self) -> None:
        for criterion in ("AC-9", "AC-1, AC-2", "CSV export"):
            with self.subTest(criterion=criterion):
                result = COVERAGE.evaluate(SPEC_TEXT, evidence(
                    check("unit-tests", criterion), check("empty", "AC-2"),
                    check("filter", "AC-3")
                ))
                self.assertEqual(result.status, "REVIEW_REQUIRED")
                self.assertTrue(result.warnings)

    def test_mixed_or_duplicate_ids_require_review(self) -> None:
        for source in (
            SPEC_TEXT.replace("- AC-3: Filter excludes unrelated rows.", "- Filter excludes unrelated rows."),
            SPEC_TEXT.replace("- AC-3: Filter excludes unrelated rows.", "- AC-2: Duplicate criterion."),
        ):
            with self.subTest(source=source):
                result = COVERAGE.evaluate(source, evidence(
                    check("export", "AC-1"), check("empty", "AC-2")
                ))
                self.assertEqual(result.status, "REVIEW_REQUIRED")
                self.assertTrue(result.warnings)

    def test_legacy_spec_skips_coverage_and_preserves_old_render(self) -> None:
        old = SPEC_TEXT.replace("AC-1: ", "").replace("AC-2: ", "").replace("AC-3: ", "")
        result = COVERAGE.evaluate(old, evidence(check("unit-tests", "AC-1")))
        self.assertFalse(result.active)
        self.assertEqual(result.status, "NOT_APPLICABLE")
        markdown = RENDERER.render_markdown(
            RENDERER.Artifact(Path("SPEC.md"), old),
            RENDERER.Artifact(Path("VERIFY.md"), "# Verify\n## Verify gate\nStatus: PASS\n"),
            RENDERER.Artifact(Path("HANDOFF.md"), None),
            RENDERER.RuntimeCheck("PASS", []), None, "main",
        )
        self.assertNotIn("Acceptance-to-evidence coverage", markdown)
        self.assertIn("Overall: **PASS**", markdown)

    def test_cli_json_is_machine_readable_and_exits_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spec = Path(tmp) / "SPEC.md"
            verify = Path(tmp) / "VERIFY.md"
            spec.write_text(SPEC_TEXT, encoding="utf-8")
            verify.write_text(evidence(check("export", "AC-1")), encoding="utf-8")
            process = subprocess.run(
                [sys.executable, str(PATH), "--spec", str(spec),
                 "--verify", str(verify), "--format", "json"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(process.returncode, 3)
            report = json.loads(process.stdout)
            self.assertEqual(report["status"], "REVIEW_REQUIRED")
            self.assertEqual(report["rows"][1]["status"], "MISSING")

    def test_multiple_checks_per_criterion_visible(self) -> None:
        result = COVERAGE.evaluate(SPEC_TEXT, evidence(
            check("positive", "AC-1"), check("negative", "AC-1"),
            check("empty", "AC-2"), check("filter", "AC-3")
        ))
        self.assertEqual(result.status, "PASS")
        self.assertEqual(result.rows[0].checks, ("positive", "negative"))

    def test_markdown_table_escapes_embedded_pipes(self) -> None:
        with_pipe = SPEC_TEXT.replace("original columns.", "original | ordered columns.")
        markdown = RENDERER.render_markdown(
            RENDERER.Artifact(Path("SPEC.md"), with_pipe),
            RENDERER.Artifact(Path("VERIFY.md"), evidence(
                check("export", "AC-1"), check("empty", "AC-2"), check("filter", "AC-3")
            )),
            RENDERER.Artifact(Path("HANDOFF.md"), None),
            RENDERER.RuntimeCheck("PASS", []), None, "main",
        )
        self.assertIn("original \\| ordered columns.", markdown)


if __name__ == "__main__":
    unittest.main()
