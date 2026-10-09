from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "eco_budget.py"


class EcoBudgetTests(unittest.TestCase):
    def check(self, *args: str, stdin: bytes | None = None) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            input=stdin, capture_output=True, check=False,
        )

    def test_combined_files_and_exact_boundary_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / "a.md", Path(tmp) / "b.md"
            a.write_text("abc", encoding="utf-8")
            b.write_text("def", encoding="utf-8")
            result = self.check("--format", "json", "--max-bytes", "6", str(a), str(b))
        self.assertEqual(result.returncode, 0)
        value = json.loads(result.stdout)
        self.assertEqual(value["status"], "PASS")
        self.assertEqual(value["selected_bytes"], 6)
        self.assertEqual(len(value["inputs"]), 2)

    def test_excess_requires_review_and_is_not_truncated(self) -> None:
        result = self.check("-", "--max-bytes", "3", stdin=b"four")
        self.assertEqual(result.returncode, 3)
        self.assertIn(b"REVIEW_REQUIRED", result.stdout)
        self.assertIn(b"4/3", result.stdout)

    def test_count_utf8_bytes_not_characters(self) -> None:
        result = self.check("-", "--max-bytes", "3", stdin="éé".encode("utf-8"))
        self.assertEqual(result.returncode, 3)

    def test_invalid_inputs_fail_closed(self) -> None:
        self.assertEqual(self.check("missing-file-eco-mode-123").returncode, 2)
        self.assertEqual(self.check("-", "--max-bytes", "0", stdin=b"a").returncode, 2)
        self.assertEqual(self.check("-", "-", stdin=b"a").returncode, 2)
        self.assertEqual(self.check("-", stdin=b"\xff").returncode, 2)

    def test_skill_contract(self) -> None:
        skill = (ROOT / "skills/eco-mode/SKILL.md").read_text(encoding="utf-8")
        for heading in ("Purpose", "When to use", "Inputs", "Workflow",
                        "Outputs", "Stop conditions", "Anti-patterns"):
            self.assertIn("## " + heading, skill)
        for anchor in ("verification evidence", "REVIEW_REQUIRED", "60,000",
                       "Haiku 5.5", "GPT-6 Luna", "silently truncate"):
            self.assertIn(anchor, skill)


if __name__ == "__main__":
    unittest.main()
