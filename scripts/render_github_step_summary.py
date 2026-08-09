#!/usr/bin/env python3
"""Publish workflow doctor and PR evidence output to GitHub Step Summary."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
DOCTOR = ROOT / "scripts" / "workflow_doctor.py"
EVIDENCE = ROOT / "scripts" / "render_pr_evidence.py"


@dataclass(frozen=True)
class ChildResult:
    name: str
    returncode: int
    stdout: str
    stderr: str


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Repository root containing workflow artifacts (default: current directory).",
    )
    parser.add_argument("--base", help="Git base passed through to doctor and evidence checks.")
    parser.add_argument("--spec", type=Path, default=Path("SPEC.md"))
    parser.add_argument("--scope", type=Path, default=Path("SCOPE.md"))
    parser.add_argument("--verify", type=Path, default=Path("VERIFY.md"))
    handoff_group = parser.add_mutually_exclusive_group()
    handoff_group.add_argument("--handoff", type=Path, default=Path("HANDOFF.md"))
    handoff_group.add_argument(
        "--no-handoff",
        action="store_true",
        help="Omit HANDOFF.md from the PR evidence renderer.",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        help="Step-summary path; defaults to $GITHUB_STEP_SUMMARY.",
    )
    return parser


def resolve_summary_path(
    explicit: Path | None,
    env: Mapping[str, str],
) -> Path | None:
    if explicit is not None:
        return explicit.expanduser().resolve()
    raw = env.get("GITHUB_STEP_SUMMARY", "").strip()
    if not raw:
        return None
    return Path(raw).expanduser().resolve()


def path_is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def run_child(name: str, argv: Sequence[str], cwd: Path) -> ChildResult:
    try:
        result = subprocess.run(
            list(argv),
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return ChildResult(
            name=name,
            returncode=127,
            stdout="",
            stderr=f"unable to run {name}: {exc}",
        )
    return ChildResult(
        name=name,
        returncode=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )


def doctor_argv(args: argparse.Namespace) -> list[str]:
    argv = [
        sys.executable,
        str(DOCTOR),
        "--root",
        str(args.root),
        "--spec",
        str(args.spec),
        "--scope",
        str(args.scope),
        "--verify",
        str(args.verify),
        "--handoff",
        str(args.handoff),
        "--format",
        "text",
    ]
    if args.base:
        argv.extend(["--base", args.base])
    return argv


def evidence_argv(args: argparse.Namespace) -> list[str]:
    argv = [
        sys.executable,
        str(EVIDENCE),
        "--spec",
        str(args.spec),
        "--verify",
        str(args.verify),
    ]
    if args.no_handoff:
        argv.append("--no-handoff")
    else:
        argv.extend(["--handoff", str(args.handoff)])
    if args.base:
        argv.extend(["--base", args.base])
    return argv


def fenced_text(result: ChildResult) -> str:
    output = result.stdout.strip()
    if not output:
        output = result.stderr.strip() or f"{result.name} produced no output"
    return output


def render_summary(doctor: ChildResult, evidence: ChildResult) -> str:
    lines = [
        "## AI Engineering Skills — Workflow Summary",
        "",
        "> Reporting only: this Step Summary preserves the underlying workflow",
        "> evidence and statuses. It does not convert review-required evidence",
        "> into success and it does not replace separate enforcement steps.",
        "",
        "### Workflow doctor",
        "",
        "```text",
        fenced_text(doctor),
        "```",
        "",
    ]

    if evidence.stdout.strip():
        lines.append(evidence.stdout.rstrip())
        lines.append("")
    else:
        lines.extend(
            [
                "## PR Evidence Summary",
                "",
                "- Evidence renderer did not produce Markdown.",
                "",
            ]
        )

    diagnostics: list[str] = []
    if doctor.stderr.strip() and doctor.stdout.strip():
        diagnostics.append(f"doctor: {doctor.stderr.strip()}")
    if evidence.stderr.strip():
        diagnostics.append(f"evidence: {evidence.stderr.strip()}")
    if doctor.returncode == 127 or evidence.returncode == 127:
        diagnostics.append("one or more child tools could not be launched")

    if diagnostics:
        lines.extend(["### Adapter diagnostics", ""])
        lines.extend(f"- {item}" for item in diagnostics)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def append_summary(path: Path, markdown: str) -> str | None:
    try:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(markdown)
    except OSError as exc:
        return f"unable to append GitHub Step Summary: {exc}"
    return None


def main(
    argv: Sequence[str] | None = None,
    *,
    env: Mapping[str, str] | None = None,
) -> int:
    args = build_parser().parse_args(argv)
    args.root = args.root.expanduser().resolve()
    summary_path = resolve_summary_path(args.summary, os.environ if env is None else env)
    if summary_path is None:
        print(
            "error: GITHUB_STEP_SUMMARY is not set; supply --summary for a local target",
            file=sys.stderr,
        )
        return 2
    if path_is_within(summary_path, args.root):
        print(
            "error: Step Summary target must be outside the repository so reporting "
            "cannot dirty live workflow state",
            file=sys.stderr,
        )
        return 2

    doctor = run_child("workflow doctor", doctor_argv(args), args.root)
    evidence = run_child("PR evidence renderer", evidence_argv(args), args.root)
    markdown = render_summary(doctor, evidence)

    error = append_summary(summary_path, markdown)
    if error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    if doctor.returncode == 127 or evidence.returncode == 127:
        print(
            "error: Step Summary published with adapter diagnostics because a child tool "
            "could not be launched",
            file=sys.stderr,
        )
        return 2

    print(f"GITHUB STEP SUMMARY: PUBLISHED -> {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
