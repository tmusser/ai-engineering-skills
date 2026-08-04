from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "render_pr_evidence.py"
SPEC = importlib.util.spec_from_file_location("render_pr_evidence", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
RENDERER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = RENDERER
SPEC.loader.exec_module(RENDERER)


SPEC_TEXT = """# Spec

## Objective

Add a safe export path.

## Acceptance criteria

- Exported rows preserve the existing schema.
- Empty results return a header-only file.

## Non-goals

- No storage migration.
"""

VERIFY_PASS = """# Verify

## Verify gate

Status: PASS

## Command evidence

- Command: python -m unittest tests.test_export
- Exit code: 0
- Relevant output: 4 tests passed
- Interpretation: export behavior matches the contract
- Acceptance criterion covered: schema and empty-result behavior
- Remaining uncertainty: none

## Build note

- Files touched: export.py, tests/test_export.py
- Tests changed: yes

## Verification

- Remaining unverified risks: none
"""

VERIFY_FAIL = VERIFY_PASS.replace("Status: PASS", "Status: FAIL")

HANDOFF = """# Handoff

## Freshness

- Snapshot commit: `abc123`
- Workspace fingerprint: `sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`

## Next recommended task

- Add the CLI smoke test.

## Verification state

- Next verification command: python -m unittest tests.test_cli
"""


class RenderPrEvidenceTests(unittest.TestCase):
    def artifact(self, name: str, text: str | None):
        return RENDERER.Artifact(Path(name), text)

    def test_verified_artifacts_render_pass_without_upgrading_language(self) -> None:
        markdown = RENDERER.render_markdown(
            self.artifact("SPEC.md", SPEC_TEXT),
            self.artifact("VERIFY.md", VERIFY_PASS),
            self.artifact("HANDOFF.md", None),
            RENDERER.RuntimeCheck("PASS", []),
            None,
            "origin/main",
        )

        self.assertIn("Overall: **PASS**", markdown)
        self.assertIn("Recorded verify gate: **PASS**", markdown)
        self.assertIn(
            "Deterministic verify gate: **PASS** against `origin/main`",
            markdown,
        )
        self.assertIn("Exported rows preserve the existing schema.", markdown)
        self.assertIn("`python -m unittest tests.test_export` — exit `0`", markdown)
        self.assertIn(
            "Files touched (artifact record): export.py, tests/test_export.py",
            markdown,
        )
        self.assertIn("No unresolved risk was recorded", markdown)

    def test_recorded_pass_without_deterministic_gate_is_review_required(self) -> None:
        gate = RENDERER.RuntimeCheck(
            "REVIEW_REQUIRED", ["deterministic verify gate not run; supply --base"]
        )
        markdown = RENDERER.render_markdown(
            self.artifact("SPEC.md", SPEC_TEXT),
            self.artifact("VERIFY.md", VERIFY_PASS),
            self.artifact("HANDOFF.md", None),
            gate,
            None,
            None,
        )

        self.assertIn("Overall: **REVIEW_REQUIRED**", markdown)
        self.assertIn(
            "Deterministic verify gate: **REVIEW_REQUIRED** (not run)",
            markdown,
        )
        self.assertIn("deterministic verify gate not run", markdown)

    def test_missing_artifacts_stay_explicitly_unestablished(self) -> None:
        markdown = RENDERER.render_markdown(
            self.artifact("SPEC.md", None),
            self.artifact("VERIFY.md", None),
            self.artifact("HANDOFF.md", None),
            RENDERER.RuntimeCheck("REVIEW_REQUIRED", ["VERIFY.md is missing"]),
            None,
            "main",
        )

        self.assertIn("Overall: **REVIEW_REQUIRED**", markdown)
        self.assertIn("Not established: SPEC objective is missing", markdown)
        self.assertIn("Not established: acceptance criteria are missing", markdown)
        self.assertIn("no complete command evidence", markdown)
        self.assertNotIn("Overall: **PASS**", markdown)

    def test_recorded_failure_cannot_be_overridden_by_passing_runtime_gate(self) -> None:
        status = RENDERER.overall_status(
            "FAIL", RENDERER.RuntimeCheck("PASS", []), None
        )
        self.assertEqual(status, "FAIL")

        markdown = RENDERER.render_markdown(
            self.artifact("SPEC.md", SPEC_TEXT),
            self.artifact("VERIFY.md", VERIFY_FAIL),
            self.artifact("HANDOFF.md", None),
            RENDERER.RuntimeCheck("PASS", []),
            None,
            "main",
        )
        self.assertIn("Overall: **FAIL**", markdown)

    def test_stale_handoff_blocks_continuation(self) -> None:
        freshness = RENDERER.RuntimeCheck(
            "REVIEW_REQUIRED",
            ["handoff is STALE; continuation state is advisory only"],
        )
        markdown = RENDERER.render_markdown(
            self.artifact("SPEC.md", SPEC_TEXT),
            self.artifact("VERIFY.md", VERIFY_PASS),
            self.artifact("HANDOFF.md", HANDOFF),
            RENDERER.RuntimeCheck("PASS", []),
            freshness,
            "main",
        )

        self.assertIn("Overall: **REVIEW_REQUIRED**", markdown)
        self.assertIn("Handoff freshness: **REVIEW_REQUIRED**", markdown)
        self.assertIn("Blocked: handoff freshness is not PASS", markdown)
        self.assertNotIn("Next task: Add the CLI smoke test.", markdown)

    def test_placeholders_are_not_rendered_as_evidence(self) -> None:
        verify = VERIFY_PASS.replace("4 tests passed", "_TBD_").replace(
            "export behavior matches the contract", "_TBD_"
        )
        records = RENDERER.command_evidence(self.artifact("VERIFY.md", verify))
        self.assertEqual(records[0]["command"], "python -m unittest tests.test_export")
        self.assertNotIn("relevant output", records[0])
        self.assertNotIn("interpretation", records[0])

    def test_template_instruction_placeholders_are_not_rendered(self) -> None:
        spec_text = """# Spec

## Objective

_Describe the smallest useful objective._

## Acceptance criteria

_Write the observable contract._
"""
        markdown = RENDERER.render_markdown(
            self.artifact("SPEC.md", spec_text),
            self.artifact("VERIFY.md", VERIFY_PASS),
            self.artifact("HANDOFF.md", None),
            RENDERER.RuntimeCheck("PASS", []),
            None,
            "main",
        )
        self.assertIn("Not established: SPEC objective is missing", markdown)
        self.assertIn("Not established: acceptance criteria are missing", markdown)
        self.assertNotIn("Describe the smallest useful objective", markdown)

    def test_output_cannot_overwrite_an_input_artifact(self) -> None:
        handoff = self.artifact("HANDOFF.md", None)
        error = RENDERER.output_path_error(
            Path("SPEC.md"), Path("SPEC.md"), Path("VERIFY.md"), handoff
        )
        self.assertIn("must not overwrite", error or "")

    def test_output_file_can_be_written_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            output = Path(tempdir) / "PR_EVIDENCE.md"
            markdown = RENDERER.render_markdown(
                self.artifact("SPEC.md", SPEC_TEXT),
                self.artifact("VERIFY.md", VERIFY_PASS),
                self.artifact("HANDOFF.md", None),
                RENDERER.RuntimeCheck("PASS", []),
                None,
                "main",
            )
            output.write_text(markdown, encoding="utf-8")
            self.assertEqual(output.read_text(encoding="utf-8"), markdown)


if __name__ == "__main__":
    unittest.main()
