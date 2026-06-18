#!/usr/bin/env python3
"""Run intentionally failing example suites under examples/**/before."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = ROOT / "examples"
MARKER = ".expect-fail"


def discover_negative_examples() -> list[Path]:
    """Return marked before-suites that should fail."""
    if not EXAMPLES_DIR.is_dir():
        raise SystemExit(f"error: examples directory not found: {EXAMPLES_DIR}")

    discovered: list[Path] = []
    for before_dir in sorted(EXAMPLES_DIR.rglob("before")):
        if not before_dir.is_dir():
            continue
        if not (before_dir / MARKER).is_file():
            continue
        if any(before_dir.rglob("test*.py")):
            discovered.append(before_dir)

    return discovered


def run_example(example_dir: Path) -> bool:
    """Run one before-suite and assert that it fails."""
    relative = example_dir.relative_to(ROOT)
    print(f"Running negative example: {relative}")
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover"],
        cwd=example_dir,
        capture_output=True,
        text=True,
    )

    if result.stdout:
        print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")

    if result.stderr:
        print(result.stderr, end="" if result.stderr.endswith("\n") else "\n", file=sys.stderr)

    if result.returncode == 0:
        print(f"error: negative example unexpectedly passed: {relative}", file=sys.stderr)
        return False

    if "Ran 0 tests" in result.stdout:
        print(f"error: negative example did not run any tests: {relative}", file=sys.stderr)
        return False

    print(f"Expected failure confirmed: {relative}")
    return True


def main() -> int:
    examples = discover_negative_examples()

    if not examples:
        print(
            "error: no negative examples found. Add a .expect-fail marker under a runnable examples/**/before suite.",
            file=sys.stderr,
        )
        return 1

    print("Discovered negative examples:")
    for example in examples:
        print(f"- {example.relative_to(ROOT)}")

    for example in examples:
        if not run_example(example):
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
