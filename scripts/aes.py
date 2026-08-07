#!/usr/bin/env python3
"""Thin command dispatcher for AI Engineering Skills repository tooling."""

from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Command:
    name: str
    summary: str
    target: Path
    runner: str = "python"
    root_cwd: bool = False


COMMANDS = {
    command.name: command
    for command in (
        Command(
            "doctor",
            "Inspect current workflow state and print the safest next move.",
            ROOT / "scripts" / "workflow_doctor.py",
        ),
        Command(
            "scope",
            "Enforce SCOPE.md against the live Git diff.",
            ROOT / "scripts" / "scope_gate.py",
        ),
        Command(
            "verify",
            "Run the deterministic verification gate.",
            ROOT / "scripts" / "verify_gate.py",
        ),
        Command(
            "evidence",
            "Render workflow artifacts into PR-ready evidence.",
            ROOT / "scripts" / "render_pr_evidence.py",
        ),
        Command(
            "context",
            "Generate an integrity-aware context packet.",
            ROOT / "scripts" / "context_pack.py",
        ),
        Command(
            "install",
            "Install or uninstall skills through the existing install wrapper.",
            ROOT / "install.sh",
            runner="sh",
            root_cwd=True,
        ),
    )
}


def print_help() -> None:
    """Print the stable dispatcher surface without reproducing child help."""
    print("AI Engineering Skills unified CLI")
    print()
    print("Usage:")
    print("  python scripts/aes.py <command> [args...]")
    print()
    print("Commands:")
    width = max(len(name) for name in COMMANDS)
    for name, command in COMMANDS.items():
        print(f"  {name:<{width}}  {command.summary}")
    print()
    print("Arguments after <command> are passed unchanged to the existing tool.")
    print("Run 'python scripts/aes.py <command> --help' for command-specific help.")


def child_argv(
    command: Command,
    forwarded: Sequence[str],
) -> tuple[list[str] | None, int | None]:
    """Build the delegated process argv or return an infrastructure exit code."""
    if not command.target.is_file():
        print(f"error: command target not found: {command.target}", file=sys.stderr)
        return None, 127

    if command.runner == "python":
        return [sys.executable, str(command.target), *forwarded], None

    if command.runner == "sh":
        shell = shutil.which("sh")
        if shell is None:
            print("error: 'sh' is required for the install command", file=sys.stderr)
            return None, 127
        return [shell, str(command.target), *forwarded], None

    print(f"error: unsupported command runner: {command.runner}", file=sys.stderr)
    return None, 127


def run(command: Command, forwarded: Sequence[str]) -> int:
    """Run one existing tool without translating its arguments or exit status."""
    argv, infrastructure_exit = child_argv(command, forwarded)
    if infrastructure_exit is not None:
        return infrastructure_exit
    assert argv is not None

    kwargs: dict[str, object] = {}
    if command.root_cwd:
        kwargs["cwd"] = ROOT

    try:
        return subprocess.call(argv, **kwargs)
    except OSError as exc:
        print(f"error: unable to run {command.name}: {exc}", file=sys.stderr)
        return 127


def main(argv: Sequence[str] | None = None) -> int:
    """Dispatch to one existing repository tool."""
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in {"-h", "--help", "help"}:
        print_help()
        return 0

    name = args[0]
    command = COMMANDS.get(name)
    if command is None:
        print(f"error: unknown command: {name}", file=sys.stderr)
        print(
            "Run 'python scripts/aes.py --help' for available commands.",
            file=sys.stderr,
        )
        return 2

    return run(command, args[1:])


if __name__ == "__main__":
    raise SystemExit(main())
