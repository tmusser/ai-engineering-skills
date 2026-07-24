from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
SKILL = ROOT / "skills" / "tool-noise-guard" / "SKILL.md"


class ToolNoiseGuardTests(unittest.TestCase):
    def test_contract_preserves_evidence_and_rejects_fake_history_compaction(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("Compact forward, not backward", text)
        self.assertIn("Never trade required evidence for token savings", text)
        self.assertIn("what new information can this call change?", text)
        self.assertIn("Do not create a `TOOL_STATE.md` ledger", text)
        self.assertIn("Claiming that compaction removed tokens already present", text)

    def test_required_skill_headings_are_present(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        for heading in (
            "## Purpose",
            "## When to use",
            "## Inputs",
            "## Workflow",
            "## Outputs",
            "## Stop conditions",
            "## Anti-patterns",
        ):
            self.assertIn(heading, text)

    def test_claude_installer_can_select_tool_noise_guard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_home:
            env = os.environ.copy()
            env["HOME"] = tmp_home
            result = subprocess.run(
                [
                    PYTHON,
                    "scripts/install_claude_code.py",
                    "--target",
                    "user",
                    "--only",
                    "tool-noise-guard",
                ],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            installed = Path(tmp_home) / ".claude" / "skills" / "tool-noise-guard" / "SKILL.md"
            self.assertTrue(installed.is_file())
            self.assertIn("Compact forward, not backward", installed.read_text(encoding="utf-8"))

    def test_codex_installer_can_select_tool_noise_guard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_home:
            env = os.environ.copy()
            env["HOME"] = tmp_home
            result = subprocess.run(
                [
                    PYTHON,
                    "scripts/install_codex.py",
                    "--target",
                    "user",
                    "--only",
                    "tool-noise-guard",
                ],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            installed = Path(tmp_home) / ".agents" / "skills" / "tool-noise-guard" / "SKILL.md"
            self.assertTrue(installed.is_file())
            self.assertIn("Never trade required evidence for token savings", installed.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
