from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


DEMO = Path(__file__).resolve().parents[1] / "run_demo.py"


class StaleHandoffDemoTests(unittest.TestCase):
    def test_naive_resume_breaks_live_code_and_guarded_resume_stops(self) -> None:
        result = subprocess.run(
            [sys.executable, str(DEMO)],
            cwd=DEMO.parent,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("NAIVE TESTS: FAIL", result.stdout)
        self.assertIn("HANDOFF FRESHNESS: STALE", result.stdout)
        self.assertIn("EDIT BLOCKED: yes", result.stdout)
        self.assertIn("GUARDED TESTS: PASS", result.stdout)
        self.assertIn("DEMO RESULT: PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
