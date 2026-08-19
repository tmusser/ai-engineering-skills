from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ACTION = ROOT / "action.yml"
RUNNER = ROOT / "scripts" / "run_github_action.sh"


class GithubActionTests(unittest.TestCase):
    def test_action_metadata_is_thin_composite_wrapper(self) -> None:
        text = ACTION.read_text(encoding="utf-8")
        self.assertIn('using: "composite"', text)
        self.assertIn("AES_BASE: ${{ inputs.base }}", text)
        self.assertIn("AES_NO_HANDOFF: ${{ inputs['no-handoff'] }}", text)
        self.assertIn('bash "$GITHUB_ACTION_PATH/scripts/run_github_action.sh"', text)
        self.assertNotIn("scope_gate.py", text)
        self.assertNotIn("verify_gate.py", text)

    def test_runner_publishes_reporting_summary_from_consumer_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            summary = Path(temp_dir) / "summary.md"
            env = os.environ.copy()
            env.update(
                {
                    "GITHUB_WORKSPACE": str(ROOT),
                    "GITHUB_STEP_SUMMARY": str(summary),
                    "AES_BASE": "",
                    "AES_NO_HANDOFF": "true",
                }
            )
            result = subprocess.run(
                ["bash", str(RUNNER)],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            rendered = summary.read_text(encoding="utf-8")
            self.assertIn("AI Engineering Skills — Workflow Summary", rendered)
            self.assertIn("Reporting only", rendered)
            self.assertIn("PR Evidence Summary", rendered)

    def test_runner_rejects_invalid_no_handoff_value(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            summary = Path(temp_dir) / "summary.md"
            env = os.environ.copy()
            env.update(
                {
                    "GITHUB_WORKSPACE": str(ROOT),
                    "GITHUB_STEP_SUMMARY": str(summary),
                    "AES_NO_HANDOFF": "sometimes",
                }
            )
            result = subprocess.run(
                ["bash", str(RUNNER)],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn("no-handoff must be 'true' or 'false'", result.stderr)
            self.assertFalse(summary.exists())


if __name__ == "__main__":
    unittest.main()
