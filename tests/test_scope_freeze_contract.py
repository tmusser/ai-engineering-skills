from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "scope-freeze" / "SKILL.md"
DOC = ROOT / "docs" / "scope-gate.md"


class ScopeFreezeContractTests(unittest.TestCase):
    def test_repo_wide_allowed_write_globs_are_forbidden(self) -> None:
        text = SKILL.read_text(encoding="utf-8")

        self.assertIn("Do not use repo-wide catch-all patterns", text)
        self.assertIn("(`*`, `**`, `**/*`)", text)
        self.assertIn("repo-wide catch-all globs are invalid scope-freeze output", text)

    def test_scope_gate_docs_surface_runtime_claim_boundary(self) -> None:
        text = DOC.read_text(encoding="utf-8")

        self.assertIn("syntactically valid globs to", text)
        self.assertIn("the gate also does not currently reject an overly broad", text.lower())
        self.assertIn("Max files changed", text)


if __name__ == "__main__":
    unittest.main()
