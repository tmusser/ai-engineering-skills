from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "spec_gate.py"
SPEC = importlib.util.spec_from_file_location("spec_gate", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
GATE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GATE
SPEC.loader.exec_module(GATE)


def complete_spec(
    *,
    acceptance: str = "- Export returns a CSV with the requested columns.",
    refs: str = "",
    open_questions: str = "- None",
) -> str:
    ref_section = ""
    if refs:
        ref_section = f"\n## Authoritative references\n\n{refs}\n"
    return f"""# Spec

## Objective

Add the requested export behavior without changing the existing API.
{ref_section}
## Acceptance criteria

{acceptance}

## Non-goals

- No schema or dependency changes.

## Spec ceiling

Do not add behavior beyond what is required by the acceptance criteria.

## Likely failure modes

Primary failure mode for this slice:

> Expanding the export surface beyond the requested format.

## Verification demo

- Run the focused export test and inspect the generated CSV header.

## Open questions

{open_questions}

## Invalid if

- Changes the existing CLI flags.
"""


class SpecGateTests(unittest.TestCase):
    def make_root(self):
        return tempfile.TemporaryDirectory()

    def write_spec(self, root: Path, text: str) -> Path:
        path = root / "SPEC.md"
        path.write_text(text, encoding="utf-8")
        return path

    def test_complete_minimal_spec_passes(self) -> None:
        with self.make_root() as tmp:
            root = Path(tmp)
            self.write_spec(root, complete_spec())
            result = GATE.evaluate(Path("SPEC.md"), root)
        self.assertEqual(result.status, "PASS")
        self.assertFalse(result.failures)
        self.assertFalse(result.review_required)

    def test_missing_spec_fails(self) -> None:
        with self.make_root() as tmp:
            result = GATE.evaluate(Path("SPEC.md"), Path(tmp))
        self.assertEqual(result.status, "FAIL")
        self.assertIn("spec not found", result.failures[0])

    def test_required_placeholder_fails(self) -> None:
        text = complete_spec().replace(
            "Add the requested export behavior without changing the existing API.",
            "_TBD_",
        )
        with self.make_root() as tmp:
            root = Path(tmp)
            self.write_spec(root, text)
            result = GATE.evaluate(Path("SPEC.md"), root)
        self.assertEqual(result.status, "FAIL")
        self.assertTrue(any("objective" in item for item in result.failures))

    def test_missing_primary_failure_mode_fails(self) -> None:
        text = complete_spec().replace(
            "> Expanding the export surface beyond the requested format.",
            "> _TBD_",
        )
        with self.make_root() as tmp:
            root = Path(tmp)
            self.write_spec(root, text)
            result = GATE.evaluate(Path("SPEC.md"), root)
        self.assertEqual(result.status, "FAIL")
        self.assertTrue(any("primary failure mode" in item for item in result.failures))

    def test_acceptance_prose_without_list_requires_review(self) -> None:
        with self.make_root() as tmp:
            root = Path(tmp)
            self.write_spec(root, complete_spec(acceptance="Export returns the requested CSV."))
            result = GATE.evaluate(Path("SPEC.md"), root)
        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertTrue(any("auditable list items" in item for item in result.review_required))

    def test_vague_acceptance_requires_review(self) -> None:
        with self.make_root() as tmp:
            root = Path(tmp)
            self.write_spec(root, complete_spec(acceptance="- Works correctly."))
            result = GATE.evaluate(Path("SPEC.md"), root)
        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertTrue(any("vague acceptance" in item for item in result.review_required))

    def test_existing_local_reference_passes(self) -> None:
        refs = """| Reference | Governs | Task-specific delta |
| --- | --- | --- |
| `tests/test_export.py::test_csv` | CSV output contract | none |"""
        with self.make_root() as tmp:
            root = Path(tmp)
            (root / "tests").mkdir()
            (root / "tests" / "test_export.py").write_text(
                "def test_csv(): pass\n",
                encoding="utf-8",
            )
            self.write_spec(root, complete_spec(refs=refs))
            result = GATE.evaluate(Path("SPEC.md"), root)
        self.assertEqual(result.status, "PASS")

    def test_missing_local_reference_fails(self) -> None:
        refs = """| Reference | Governs | Task-specific delta |
| --- | --- | --- |
| `tests/test_missing.py` | CSV output contract | none |"""
        with self.make_root() as tmp:
            root = Path(tmp)
            self.write_spec(root, complete_spec(refs=refs))
            result = GATE.evaluate(Path("SPEC.md"), root)
        self.assertEqual(result.status, "FAIL")
        self.assertTrue(any("reference not found" in item for item in result.failures))

    def test_placeholder_reference_row_requires_review(self) -> None:
        refs = """| Reference | Governs | Task-specific delta |
| --- | --- | --- |
| _file, test, symbol, artifact, URL, rubric, or source implementation_ | _behavior/decision_ | _none or explicit difference_ |"""
        with self.make_root() as tmp:
            root = Path(tmp)
            self.write_spec(root, complete_spec(refs=refs))
            result = GATE.evaluate(Path("SPEC.md"), root)
        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertTrue(any("placeholder" in item for item in result.review_required))

    def test_open_question_placeholder_requires_review(self) -> None:
        with self.make_root() as tmp:
            root = Path(tmp)
            self.write_spec(root, complete_spec(open_questions="- _TBD_"))
            result = GATE.evaluate(Path("SPEC.md"), root)
        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertTrue(any("placeholder" in item for item in result.review_required))

    def test_unresolved_open_question_requires_review(self) -> None:
        with self.make_root() as tmp:
            root = Path(tmp)
            self.write_spec(
                root,
                complete_spec(open_questions="- Should the existing JSON output also change?"),
            )
            result = GATE.evaluate(Path("SPEC.md"), root)
        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertTrue(any("open questions" in item for item in result.review_required))

    def test_main_exit_policy_preserves_human_review_default(self) -> None:
        with self.make_root() as tmp:
            root = Path(tmp)
            self.write_spec(root, complete_spec(acceptance="- Works correctly."))
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(GATE.main(["--root", str(root)]), 0)
                self.assertEqual(
                    GATE.main(["--root", str(root), "--strict-review"]),
                    2,
                )

    def test_json_output_contains_checks_and_status(self) -> None:
        with self.make_root() as tmp:
            root = Path(tmp)
            self.write_spec(root, complete_spec())
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                status = GATE.main(["--root", str(root), "--format", "json"])
        self.assertEqual(status, 0)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["status"], "PASS")
        self.assertTrue(payload["checks"])


if __name__ == "__main__":
    unittest.main()
