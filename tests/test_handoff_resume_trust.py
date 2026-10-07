from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESUME = ROOT / "skills" / "handoff" / "scripts" / "resume_trust.py"
FRESHNESS = ROOT / "skills" / "handoff" / "scripts" / "handoff_freshness.py"
PYTHON = sys.executable

VERIFY_PASS = """# Verify

## Verify gate

Status: PASS
"""

VERIFY_REVIEW = VERIFY_PASS.replace("Status: PASS", "Status: REVIEW_REQUIRED")

HANDOFF = """# Handoff

## Freshness

- Snapshot commit: `_TBD_`
- Workspace fingerprint: `_TBD_`

## Resume packet

- Required resume files: SPEC.md, VERIFY.md

## Continuation guardrails

- Verify gate status: PASS
- Review-required items: none

## Verification state

Next verification command: python -m unittest

## Next recommended task

- Add the CLI wrapper.
"""


def run(script: Path, *args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, str(script), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)


class HandoffResumeTrustTests(unittest.TestCase):
    def make_repo(
        self,
        *,
        verify: str = VERIFY_PASS,
        handoff: str = HANDOFF,
    ) -> Path:
        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        root = Path(tempdir.name)
        git(root, "init", "-q")
        git(root, "config", "user.email", "test@example.com")
        git(root, "config", "user.name", "Test User")
        (root / "SPEC.md").write_text("# Spec\n", encoding="utf-8")
        (root / "VERIFY.md").write_text(verify, encoding="utf-8")
        (root / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
        (root / "HANDOFF.md").write_text(handoff, encoding="utf-8")
        git(root, "add", ".")
        git(root, "commit", "-qm", "initial")
        stamped = run(FRESHNESS, "stamp", "--root", str(root), cwd=root)
        self.assertEqual(stamped.returncode, 0, stamped.stdout + stamped.stderr)
        return root

    def check(self, root: Path) -> subprocess.CompletedProcess[str]:
        return run(RESUME, "check", "--root", str(root), cwd=root)

    def test_fresh_coherent_handoff_passes(self) -> None:
        root = self.make_repo()
        result = self.check(root)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("HANDOFF RESUME TRUST: PASS", result.stdout)

    def test_missing_required_resume_file_requires_review(self) -> None:
        root = self.make_repo(
            handoff=HANDOFF.replace(
                "SPEC.md, VERIFY.md",
                "SPEC.md, VERIFY.md, docs/missing.md",
            )
        )
        result = self.check(root)
        self.assertEqual(result.returncode, 3)
        self.assertIn("required resume file missing: docs/missing.md", result.stdout)

    def test_verification_status_mismatch_requires_review(self) -> None:
        root = self.make_repo(verify=VERIFY_REVIEW)
        result = self.check(root)
        self.assertEqual(result.returncode, 3)
        self.assertIn(
            "verification status mismatch: handoff=PASS, live=REVIEW_REQUIRED",
            result.stdout,
        )
        self.assertIn(
            "Review-required items: none but live verification is REVIEW_REQUIRED",
            result.stdout,
        )

    def test_stale_review_items_require_reconciliation(self) -> None:
        root = self.make_repo(
            handoff=HANDOFF.replace(
                "Review-required items: none",
                "Review-required items: confirm migration behavior",
            )
        )
        result = self.check(root)
        self.assertEqual(result.returncode, 3)
        self.assertIn(
            "handoff carries review-required items but live verification status is PASS",
            result.stdout,
        )

    def test_multiple_next_tasks_require_review(self) -> None:
        root = self.make_repo(
            handoff=HANDOFF.replace(
                "- Add the CLI wrapper.",
                "- Add the CLI wrapper.\n- Refactor config.",
            )
        )
        result = self.check(root)
        self.assertEqual(result.returncode, 3)
        self.assertIn("expected exactly one next recommended task, found 2", result.stdout)

    def test_missing_next_verification_command_requires_review(self) -> None:
        root = self.make_repo(
            handoff=HANDOFF.replace(
                "Next verification command: python -m unittest",
                "Next verification command: _TBD_",
            )
        )
        result = self.check(root)
        self.assertEqual(result.returncode, 3)
        self.assertIn("missing Next verification command", result.stdout)

    def test_workspace_change_is_stale_before_content_is_trusted(self) -> None:
        root = self.make_repo()
        (root / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
        result = self.check(root)
        self.assertEqual(result.returncode, 2)
        self.assertIn("HANDOFF RESUME TRUST: STALE", result.stdout)


if __name__ == "__main__":
    unittest.main()
