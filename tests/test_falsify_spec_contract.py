from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "falsify-spec" / "SKILL.md"
EXAMPLE = ROOT / "examples" / "spec-falsifier"


class SpecFalsifierContractTests(unittest.TestCase):
    def test_skill_is_optional_and_has_all_required_sections(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\nname: falsify-spec\n"))
        for heading in (
            "Purpose", "When to use", "Inputs", "Workflow", "Outputs",
            "Stop conditions", "Anti-patterns",
        ):
            self.assertIn(f"## {heading}", text)
        for phrase in (
            "Do not activate merely because", "at most three",
            "SOURCE_BACKED", "HYPOTHESIS", "DECISION_REQUIRED",
            "smallest discriminator", "before implementation",
            "NONE_FOUND", "does not prove the spec is complete",
            "Do not create", "spec_gate.py",
        ):
            self.assertIn(phrase, text)

    def test_both_specs_pass_structural_gate_but_only_one_covers_no_matches(self) -> None:
        for name in ("weak-SPEC.md", "strengthened-SPEC.md"):
            with self.subTest(spec=name):
                result = subprocess.run(
                    [
                        sys.executable, str(ROOT / "scripts" / "spec_gate.py"),
                        "--root", str(ROOT), "--spec",
                        f"examples/spec-falsifier/{name}",
                        "--strict-review", "--format", "json",
                    ],
                    check=False, capture_output=True, text=True,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(json.loads(result.stdout)["status"], "PASS")

        weak = (EXAMPLE / "weak-SPEC.md").read_text(encoding="utf-8")
        strong = (EXAMPLE / "strengthened-SPEC.md").read_text(encoding="utf-8")
        self.assertNotIn("header-only", weak)
        self.assertIn("zero matching orders", strong)
        self.assertIn("header-only", strong)
        self.assertIn("assert header-only output", strong)

    def test_example_links_counterfeit_to_source_and_discriminator(self) -> None:
        text = (EXAMPLE / "README.md").read_text(encoding="utf-8")
        for phrase in (
            "Original request", "header-only CSV response",
            "region=\"Antarctica\"", "return \"\"",
            "SOURCE_BACKED", "Verdict: FOUND", "Discriminator:",
            "Proposed SPEC delta:", "not measured improvements",
        ):
            self.assertIn(phrase, text)

    def test_existing_starting_routes_remain_unchanged(self) -> None:
        bundles = (ROOT / "docs" / "bundles.md").read_text(encoding="utf-8")
        starter = bundles.split("## Starter\n", 1)[1].split("## Bugfix\n", 1)[0]
        self.assertNotIn("falsify-spec", starter)
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("mini-spec -> scope-freeze -> build-one -> verify-contract -> handoff", readme)


if __name__ == "__main__":
    unittest.main()
