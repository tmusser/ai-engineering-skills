from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "teach-back" / "SKILL.md"
DOC = ROOT / "docs" / "teach-back.md"
EXAMPLE = ROOT / "examples" / "teach-back-example.md"


class TeachBackSkillTests(unittest.TestCase):
    def test_skill_keeps_optional_post_verification_boundary(self) -> None:
        text = SKILL.read_text(encoding="utf-8")

        self.assertIn("name: teach-back", text)
        self.assertIn("Transfer ownership, do not narrate the diff.", text)
        self.assertIn("Test understanding, do not assume it.", text)
        self.assertIn("This skill is optional.", text)
        self.assertIn("If correctness is unresolved", text)
        self.assertIn("route to `verify-contract` or diagnosis first", text)

    def test_skill_requires_grounded_attempt_before_explanation(self) -> None:
        text = SKILL.read_text(encoding="utf-8")

        self.assertIn("Ask the human for a short teach-back attempt before giving the full explanation", text)
        self.assertIn("**Observed**", text)
        self.assertIn("**Inferred**", text)
        self.assertIn("**Open**", text)
        self.assertIn("prediction, debugging, or modification", text)

    def test_skill_does_not_make_learning_artifacts_mandatory(self) -> None:
        text = SKILL.read_text(encoding="utf-8")

        self.assertIn("Create `LEARN.md` only when", text)
        self.assertIn("Creating `LEARN.md` for every task", text)
        self.assertIn("Asking for private chain-of-thought", text)

    def test_supporting_docs_and_example_exist(self) -> None:
        self.assertTrue(DOC.is_file())
        self.assertTrue(EXAMPLE.is_file())

        doc_text = DOC.read_text(encoding="utf-8")
        example_text = EXAMPLE.read_text(encoding="utf-8")

        self.assertIn("build-one -> verify-contract -> teach-back -> handoff", doc_text)
        self.assertIn("Treat `teach-back` as an experimental workflow hypothesis", doc_text)
        self.assertIn("## Transfer question", example_text)
        self.assertIn("## Ownership check", example_text)


if __name__ == "__main__":
    unittest.main()
