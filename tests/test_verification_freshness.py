from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
SCRIPT = ROOT / "skills" / "verify-contract" / "scripts" / "verification_freshness.py"


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True)
    return result.stdout.strip()


class VerificationFreshnessTests(unittest.TestCase):
    def make_repo(self) -> Path:
        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        root = Path(tempdir.name)
        git(root, "init")
        git(root, "config", "user.name", "Test User")
        git(root, "config", "user.email", "test@example.com")
        (root / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
        (root / "VERIFY.md").write_text(
            "# Verify\n\n## Verification freshness\n\n"
            "- Snapshot commit: \`_TBD_\`\n"
            "- Workspace fingerprint: \`_TBD_\`\n",
            encoding="utf-8",
        )
        git(root, "add", ".")
        git(root, "commit", "-qm", "base")
        return root

    def run_script(self, root: Path, command: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [PYTHON, str(SCRIPT), command, "--root", str(root), "--verify", "VERIFY.md"],
            cwd=root,
            capture_output=True,
            text=True,
        )

    def test_stamp_then_check_passes(self) -> None:
        root = self.make_repo()
        stamped = self.run_script(root, "stamp")
        self.assertEqual(stamped.returncode, 0, stamped.stdout + stamped.stderr)
        checked = self.run_script(root, "check")
        self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
        self.assertIn("VERIFICATION FRESHNESS: PASS", checked.stdout)

    def test_source_change_after_stamp_is_stale(self) -> None:
        root = self.make_repo()
        self.assertEqual(self.run_script(root, "stamp").returncode, 0)
        (root / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
        checked = self.run_script(root, "check")
        self.assertEqual(checked.returncode, 2)
        self.assertIn("VERIFICATION FRESHNESS: STALE", checked.stdout)

    def test_committing_only_verify_does_not_make_it_stale(self) -> None:
        root = self.make_repo()
        self.assertEqual(self.run_script(root, "stamp").returncode, 0)
        git(root, "add", "VERIFY.md")
        git(root, "commit", "-qm", "record verification")
        checked = self.run_script(root, "check")
        self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
        self.assertIn("HEAD moved", checked.stdout)

    def test_missing_anchors_requires_review(self) -> None:
        root = self.make_repo()
        (root / "VERIFY.md").write_text("# Verify\n\nNo freshness anchors.\n", encoding="utf-8")
        checked = self.run_script(root, "check")
        self.assertEqual(checked.returncode, 3)
        self.assertIn("REVIEW_REQUIRED", checked.stdout)


if __name__ == "__main__":
    unittest.main()
