from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROPOSE = ROOT / "scripts" / "context_manifest.py"
ECO = ROOT / "scripts" / "eco_budget.py"

SPEC = """# Spec

## Objective

Add a safe region filter.

## Authoritative references

| Reference | Governs | Task-specific delta |
| --- | --- | --- |
| docs/export-contract.md | CSV schema | none |
| tests/test_export.py | Zero match behavior | none |

## Acceptance criteria

- AC-1: Header-only CSV for zero matches.

## Invalid if

- Existing columns change.

## Commands

- Test: python -m pytest tests/test_export.py
"""


class ContextManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root / "docs").mkdir()
        (self.root / "tests").mkdir()
        self.spec = self.root / "SPEC.md"
        self.rule = self.root / "docs/export-contract.md"
        self.test_file = self.root / "tests/test_export.py"
        self.manifest = self.root / "coverage.json"
        self.spec.write_text(SPEC, encoding="utf-8")
        self.rule.write_text("# Export contract\n\nAlways keep original columns.\n", encoding="utf-8")
        self.test_file.write_text("def test_empty(): pass\n", encoding="utf-8")

    def run_propose(self, *args: str):
        return subprocess.run(
            [sys.executable, str(PROPOSE), "--root", str(self.root),
             "--spec", "SPEC.md", *args],
            text=True, capture_output=True, check=False,
        )

    def run_eco(self, *args: str) -> tuple[int, dict]:
        run = subprocess.run(
            [sys.executable, str(ECO), "--root", str(self.root),
             "--format", "json", *args],
            text=True, capture_output=True, check=False,
        )
        if run.returncode == 2:
            return 2, {"error": run.stderr}
        return run.returncode, json.loads(run.stdout)

    def save(self, manifest: dict) -> None:
        self.manifest.write_text(json.dumps(manifest), encoding="utf-8")

    def propose(self) -> dict:
        run = self.run_propose("--output", str(self.manifest))
        self.assertEqual(run.returncode, 0, run.stderr)
        return json.loads(self.manifest.read_text(encoding="utf-8"))

    def test_proposal_contains_only_explicit_sources_and_proof(self) -> None:
        proposed = self.propose()
        self.assertFalse(proposed["approved"])
        self.assertEqual(proposed["schema_version"], 1)
        self.assertEqual(
            proposed["required_sources"],
            ["SPEC.md", "docs/export-contract.md", "tests/test_export.py"],
        )
        self.assertEqual(
            proposed["required_headings"],
            ["SPEC.md::Acceptance criteria", "SPEC.md::Invalid if"],
        )
        self.assertEqual(proposed["required_proofs"], ["python -m pytest tests/test_export.py"])
        self.assertEqual(proposed["unresolved"], [])
        self.assertTrue(proposed["spec_sha256"].startswith("sha256:"))

    def test_proposed_manifest_requires_approval_then_passes(self) -> None:
        proposed = self.propose()
        selected = (str(self.spec), str(self.rule), str(self.test_file))
        code, report = self.run_eco(*selected, "--manifest", str(self.manifest))
        self.assertEqual(code, 3)
        self.assertIn("operator must review", str(report["sufficiency"]["warnings"]))
        proposed["approved"] = True
        self.save(proposed)
        code, report = self.run_eco(*selected, "--manifest", str(self.manifest))
        self.assertEqual(code, 0, report)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(len(report["sufficiency"]["sources"]), 3)
        self.assertEqual(len(report["sufficiency"]["headings"]), 2)
        self.assertEqual(report["sufficiency"]["proofs"][0]["status"], "represented")

    def test_changes_to_spec_invalidate_approved_manifest(self) -> None:
        proposed = self.propose()
        proposed["approved"] = True
        self.save(proposed)
        self.spec.write_text(SPEC + "\nMore details.\n", encoding="utf-8")
        code, report = self.run_eco(str(self.spec), str(self.rule), str(self.test_file),
                                    "--manifest", str(self.manifest))
        self.assertEqual(code, 3)
        self.assertIn("manifest stale", str(report["sufficiency"]["warnings"]))

    def test_missing_explicit_reference_is_unresolved_not_guessed(self) -> None:
        self.spec.write_text(
            SPEC.replace("tests/test_export.py | Zero", "tests/does_not_exist.py | Zero"),
            encoding="utf-8",
        )
        proposed = self.propose()
        self.assertNotIn("tests/does_not_exist.py", proposed["required_sources"])
        self.assertTrue(any("reference missing" in text for text in proposed["unresolved"]))
        proposed["approved"] = True
        self.save(proposed)
        code, report = self.run_eco(str(self.spec), str(self.rule),
                                    "--manifest", str(self.manifest))
        self.assertEqual(code, 3)
        self.assertIn("unresolved", str(report["sufficiency"]["warnings"]))

    def test_external_or_ambiguous_refs_are_not_promoted(self) -> None:
        self.spec.write_text(SPEC.replace(
            "| tests/test_export.py | Zero match behavior | none |",
            "| https://example.com/spec | Zero match behavior | none |",
        ), encoding="utf-8")
        proposed = self.propose()
        self.assertEqual(proposed["required_sources"], ["SPEC.md", "docs/export-contract.md"])
        self.assertTrue(any("not an exact local path" in line for line in proposed["unresolved"]))

    def test_missing_sources_and_proof_require_review(self) -> None:
        proposed = self.propose()
        proposed["approved"] = True
        self.save(proposed)
        code, report = self.run_eco(str(self.rule), "--manifest", str(self.manifest))
        self.assertEqual(code, 3)
        self.assertTrue(any(item["status"] == "missing"
                            for item in report["sufficiency"]["sources"]))
        self.assertEqual(report["sufficiency"]["proofs"][0]["status"], "missing")

    def test_stricter_cli_requirements_are_not_dropped(self) -> None:
        proposed = self.propose()
        proposed["approved"] = True
        self.save(proposed)
        code, report = self.run_eco(
            str(self.spec), str(self.rule), str(self.test_file),
            "--manifest", str(self.manifest),
            "--require-proof", "missing additional proof",
        )
        self.assertEqual(code, 3)
        self.assertTrue(any(item["status"] == "missing"
                            for item in report["sufficiency"]["proofs"]))

    def test_broken_schema_and_unsafe_paths_are_errors(self) -> None:
        proposed = self.propose()
        for change in (
            {"approved": "yes"},
            {"schema_version": 2},
            {"required_sources": ["../secret.md", "SPEC.md"]},
            {"required_sources": ["docs/export-contract.md"]},
            {"extra": 1},
        ):
            with self.subTest(change=change):
                malformed = {**proposed, **change}
                self.save(malformed)
                code, _ = self.run_eco(str(self.spec), "--manifest", str(self.manifest))
                self.assertEqual(code, 2)

    def test_manifest_cannot_satisfy_its_own_proof_anchors(self) -> None:
        self.propose()
        code, report = self.run_eco(str(self.manifest), "--manifest", str(self.manifest))
        self.assertEqual(code, 2)
        self.assertIn("must not be included", report["error"])

    def test_byte_only_mode_unchanged_without_manifest(self) -> None:
        code, report = self.run_eco(str(self.spec))
        self.assertEqual(code, 0)
        self.assertNotIn("sufficiency", report)

    def test_unavailable_spec_after_approval_needs_review(self) -> None:
        proposed = self.propose()
        proposed["approved"] = True
        self.save(proposed)
        self.spec.unlink()
        code, report = self.run_eco(str(self.rule), "--manifest", str(self.manifest))
        self.assertEqual(code, 3, report)
        self.assertTrue(report["sufficiency"]["warnings"])

    def test_never_overwrites_input_spec(self) -> None:
        result = self.run_propose("--output", str(self.spec))
        self.assertEqual(result.returncode, 2)
        self.assertEqual(self.spec.read_text(encoding="utf-8"), SPEC)


if __name__ == "__main__":
    unittest.main()
