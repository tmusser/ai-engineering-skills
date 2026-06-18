#!/usr/bin/env python3
"""Run runnable example suites under examples/**/after."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = ROOT / "examples"


def discover_runnable_examples() -> list[Path]:
    """Return example directories that have runnable after-suites."""
    if not EXAMPLES_DIR.is_dir():
        raise SystemExit(f"error: examples directory not found: {EXAMPLES_DIR}")

    discovered: list[Path] = []
    for after_dir in sorted(EXAMPLES_DIR.rglob("after")):
        if not after_dir.is_dir():
            continue
        if any(after_dir.rglob("test*.py")):
            discovered.append(after_dir)

    return discovered


def run_example(example_dir: Path) -> bool:
    """Run one after-suite and print its output."""
    relative = example_dir.relative_to(ROOT)
    print(f"Running runnable example: {relative}")
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

    if result.returncode != 0:
        print(f"error: runnable example failed: {relative}", file=sys.stderr)
        return False

    if "Ran 0 tests" in result.stdout:
        print(f"error: runnable example did not run any tests: {relative}", file=sys.stderr)
        return False

    return True


def main() -> int:
    examples = discover_runnable_examples()

    if not examples:
        print("error: no runnable examples found under examples/**/after", file=sys.stderr)
        return 1

    print("Discovered runnable examples:")
    for example in examples:
        print(f"- {example.relative_to(ROOT)}")

    for example in examples:
        if not run_example(example):
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
