#!/usr/bin/env python3
"""Demonstrate why a stale handoff must not outrank live repository state."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
FRESHNESS_GUARD = REPO_ROOT / "skills" / "handoff" / "scripts" / "handoff_freshness.py"
PYTHON = sys.executable

INITIAL_MODULE = '''def normalize_customer_id(raw: str) -> str:
    """Return the legacy uppercase customer id."""
    return raw.strip().upper()
'''

INITIAL_TEST = '''import unittest

from customer_ids import normalize_customer_id


class CustomerIdTests(unittest.TestCase):
    def test_normalizes_legacy_id(self) -> None:
        self.assertEqual(normalize_customer_id(" cus-17 "), "CUS-17")


if __name__ == "__main__":
    unittest.main()
'''

LIVE_MODULE = '''def parse_customer_id(raw: str) -> str:
    """Validate and return the canonical customer id."""
    value = raw.strip().upper()
    if not value.startswith("CUS-"):
        raise ValueError("customer id must start with CUS-")
    return value
'''

LIVE_TEST = '''import unittest

import customer_ids
from customer_ids import parse_customer_id


class CustomerIdTests(unittest.TestCase):
    def test_parses_canonical_id(self) -> None:
        self.assertEqual(parse_customer_id(" cus-17 "), "CUS-17")

    def test_rejects_non_customer_id(self) -> None:
        with self.assertRaises(ValueError):
            parse_customer_id("admin-17")

    def test_legacy_api_stays_removed(self) -> None:
        self.assertFalse(hasattr(customer_ids, "normalize_customer_id"))


if __name__ == "__main__":
    unittest.main()
'''

HANDOFF = '''# Handoff

## Freshness

- Snapshot commit: `_TBD_`
- Workspace fingerprint: `_TBD_`

## Resume packet

- Status: legacy normalizer is current
- Next task: add prefix validation to `normalize_customer_id`
- Verification: `python -m unittest discover -s tests`
'''

STALE_EDIT = '''\n\ndef normalize_customer_id(raw: str) -> str:
    """Legacy API resurrected by following stale continuation state."""
    value = raw.strip().upper()
    if not value.startswith("CUS-"):
        raise ValueError("customer id must start with CUS-")
    return value
'''


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)


def git(root: Path, *args: str) -> None:
    result = run(["git", *args], root)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def freshness(root: Path, command: str) -> subprocess.CompletedProcess[str]:
    return run(
        [PYTHON, str(FRESHNESS_GUARD), command, "--root", str(root)],
        root,
    )


def tests(root: Path) -> subprocess.CompletedProcess[str]:
    return run([PYTHON, "-m", "unittest", "discover", "-s", "tests"], root)


def build_stale_repo(root: Path) -> None:
    git(root, "init", "-q")
    git(root, "config", "user.email", "demo@example.com")
    git(root, "config", "user.name", "Stale Handoff Demo")
    write(root / "customer_ids.py", INITIAL_MODULE)
    write(root / "tests" / "test_customer_ids.py", INITIAL_TEST)
    write(root / "HANDOFF.md", HANDOFF)
    git(root, "add", ".")
    git(root, "commit", "-qm", "initial legacy normalizer")

    stamped = freshness(root, "stamp")
    if stamped.returncode != 0:
        raise RuntimeError(stamped.stderr.strip() or stamped.stdout.strip())
    git(root, "add", "HANDOFF.md")
    git(root, "commit", "-qm", "record continuation handoff")

    write(root / "customer_ids.py", LIVE_MODULE)
    write(root / "tests" / "test_customer_ids.py", LIVE_TEST)
    git(root, "add", "customer_ids.py", "tests/test_customer_ids.py")
    git(root, "commit", "-qm", "replace legacy normalizer with validated parser")


def apply_naive_resume(root: Path) -> subprocess.CompletedProcess[str]:
    with (root / "customer_ids.py").open("a", encoding="utf-8") as handle:
        handle.write(STALE_EDIT)
    return tests(root)


def apply_guarded_resume(
    root: Path,
) -> tuple[subprocess.CompletedProcess[str], subprocess.CompletedProcess[str], bool]:
    source = root / "customer_ids.py"
    before = source.read_bytes()
    checked = freshness(root, "check")
    if checked.returncode == 0:
        with source.open("a", encoding="utf-8") as handle:
            handle.write(STALE_EDIT)
    unchanged = source.read_bytes() == before
    return checked, tests(root), unchanged


def run_demo() -> bool:
    if not FRESHNESS_GUARD.is_file():
        raise RuntimeError(f"missing bundled freshness guard: {FRESHNESS_GUARD}")

    with tempfile.TemporaryDirectory() as tempdir:
        temp = Path(tempdir)
        seed = temp / "seed"
        seed.mkdir()
        build_stale_repo(seed)
        naive = temp / "naive"
        guarded = temp / "guarded"
        shutil.copytree(seed, naive)
        shutil.copytree(seed, guarded)

        naive_tests = apply_naive_resume(naive)
        guarded_check, guarded_tests, guarded_unchanged = apply_guarded_resume(guarded)

        print("NAIVE RESUME")
        print("- trusted stale next task: modify normalize_customer_id")
        print("- edit: resurrected the removed legacy API")
        print(f"- NAIVE TESTS: {'PASS' if naive_tests.returncode == 0 else 'FAIL'}")
        print()
        print("GUARDED RESUME")
        print(guarded_check.stdout.strip())
        print(f"- EDIT BLOCKED: {'yes' if guarded_unchanged else 'no'}")
        print(f"- GUARDED TESTS: {'PASS' if guarded_tests.returncode == 0 else 'FAIL'}")

        passed = (
            naive_tests.returncode != 0
            and guarded_check.returncode == 2
            and guarded_unchanged
            and guarded_tests.returncode == 0
        )
        print()
        print(f"DEMO RESULT: {'PASS' if passed else 'FAIL'}")
        return passed


def main() -> int:
    try:
        return 0 if run_demo() else 1
    except (OSError, RuntimeError) as exc:
        print(f"DEMO RESULT: ERROR\n- {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
