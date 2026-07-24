from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "handoff_freshness.py"
PYTHON = sys.executable
TEMPLATE = """# Handoff

## Freshness

- Snapshot commit: `_TBD_`
- Workspace fingerprint: `_TBD_`

## Resume packet

- Next task: continue safely
"""


def run(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, str(SCRIPT), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True
    )


class HandoffFreshnessTests(unittest.TestCase):
    def make_repo(self) -> Path:
        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        root = Path(tempdir.name)
        git(root, "init", "-q")
        git(root, "config", "user.email", "test@example.com")
        git(root, "config", "user.name", "Test User")
        (root / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
        (root / "HANDOFF.md").write_text(TEMPLATE, encoding="utf-8")
        git(root, "add", ".")
        git(root, "commit", "-qm", "initial")
        return root

    def stamp(self, root: Path) -> subprocess.CompletedProcess[str]:
        return run("stamp", "--root", str(root), cwd=root)

    def check(self, root: Path) -> subprocess.CompletedProcess[str]:
        return run("check", "--root", str(root), cwd=root)

    def test_stamped_handoff_passes(self) -> None:
        root = self.make_repo()
        stamped = self.stamp(root)
        self.assertEqual(stamped.returncode, 0, stamped.stderr)
        result = self.check(root)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("HANDOFF FRESHNESS: PASS", result.stdout)

    def test_tracked_worktree_change_marks_handoff_stale(self) -> None:
        root = self.make_repo()
        self.assertEqual(self.stamp(root).returncode, 0)
        (root / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
        result = self.check(root)
        self.assertEqual(result.returncode, 2)
        self.assertIn("HANDOFF FRESHNESS: STALE", result.stdout)

    def test_untracked_file_marks_handoff_stale(self) -> None:
        root = self.make_repo()
        self.assertEqual(self.stamp(root).returncode, 0)
        (root / "notes.txt").write_text("new state\n", encoding="utf-8")
        result = self.check(root)
        self.assertEqual(result.returncode, 2)
        self.assertIn("HANDOFF FRESHNESS: STALE", result.stdout)

    def test_handoff_edits_do_not_invalidate_their_own_snapshot(self) -> None:
        root = self.make_repo()
        self.assertEqual(self.stamp(root).returncode, 0)
        with (root / "HANDOFF.md").open("a", encoding="utf-8") as handle:
            handle.write("\n- Clarification added after stamping.\n")
        result = self.check(root)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("HANDOFF FRESHNESS: PASS", result.stdout)

    def test_committing_only_the_handoff_does_not_make_it_stale(self) -> None:
        root = self.make_repo()
        self.assertEqual(self.stamp(root).returncode, 0)
        git(root, "add", "HANDOFF.md")
        git(root, "commit", "-qm", "record handoff")
        result = self.check(root)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("HEAD moved", result.stdout)

    def test_committed_project_change_marks_handoff_stale(self) -> None:
        root = self.make_repo()
        self.assertEqual(self.stamp(root).returncode, 0)
        (root / "app.py").write_text("VALUE = 3\n", encoding="utf-8")
        git(root, "add", "app.py")
        git(root, "commit", "-qm", "change app")
        result = self.check(root)
        self.assertEqual(result.returncode, 2)
        self.assertIn("HANDOFF FRESHNESS: STALE", result.stdout)

    def test_missing_anchors_requires_review(self) -> None:
        root = self.make_repo()
        (root / "HANDOFF.md").write_text("# Handoff\n\nNo freshness block.\n", encoding="utf-8")
        result = self.check(root)
        self.assertEqual(result.returncode, 3)
        self.assertIn("REVIEW_REQUIRED", result.stdout)


if __name__ == "__main__":
    unittest.main()
