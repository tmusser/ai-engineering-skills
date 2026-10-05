from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class OperatorProfileContractTests(unittest.TestCase):
    def read(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_profile_is_setup_only_and_cannot_expand_authority(self) -> None:
        text = self.read("skills/operator-profile/SKILL.md")
        self.assertIn("Setup skill, not a workflow stage.", text)
        self.assertIn("The profile may narrow authority; it may not grant new authority.", text)
        self.assertIn("Do not create `OPERATOR.md` by default.", text)
        self.assertIn("Ceremony preference: `lean | balanced | guarded`", text)
        self.assertIn("Autonomy boundary: `propose-only | bounded-execution | human-gate-side-effects`", text)
        self.assertIn("Verification depth: `targeted | standard | expanded`", text)
        self.assertIn("Communication density: `lean | normal | explanatory`", text)
        self.assertIn("Ambiguity handling: `ask-material | safe-reversible-assumptions`", text)

    def test_existing_skills_consume_profile_without_weakening_contracts(self) -> None:
        ceremony = self.read("skills/ceremony-budget/SKILL.md")
        lean = self.read("skills/lean-mode/SKILL.md")
        verify = self.read("skills/verify-contract/SKILL.md")
        ship = self.read("skills/ship-mini/SKILL.md")

        self.assertIn("Operator profile is a tie-breaker, not a risk override.", ceremony)
        self.assertIn("Communication density", lean)
        self.assertIn("Verification depth", verify)
        self.assertIn("Autonomy boundary", ship)
        self.assertIn("does not grant activation permission", ship)


if __name__ == "__main__":
    unittest.main()
