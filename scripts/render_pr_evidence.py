#!/usr/bin/env python3
"""Render workflow artifacts into a review-safe pull request evidence summary."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SPEC = Path("SPEC.md")
DEFAULT_VERIFY = Path("VERIFY.md")
DEFAULT_HANDOFF = Path("HANDOFF.md")
VERIFY_GATE = ROOT / "scripts" / "verify_gate.py"
HANDOFF_FRESHNESS = (
    ROOT / "skills" / "handoff" / "scripts" / "handoff_freshness.py"
)
VALID_STATUSES = {"PASS", "FAIL", "REVIEW_REQUIRED"}
PLACEHOLDER_VALUES = {
    "",
    "-",
    "_tbd_",
    "tbd",
    "none",
    "n/a",
    "yes/no",
    "pass | fail | review_required",
}
HEADING_RE = re.compile(r"^(?P<marks>#{1,6})\s+(?P<title>.+?)\s*$")
STATUS_RE = re.compile(r"(?im)^\s*Status\s*:\s*(PASS|FAIL|REVIEW_REQUIRED)\s*$")
FIELD_RE = re.compile(r"^\s*[-*+]\s*(?P<label>[^:]+):\s*(?P<value>.*)\s*$")


@dataclass(frozen=True)
class RuntimeCheck:
    status: str
    details: list[str]
    changed_files: tuple[str, ...] = ()
    checks: tuple[str, ...] = ()


@dataclass(frozen=True)
class Artifact:
    path: Path
    text: str | None

    @property
    def present(self) -> bool:
        return self.text is not None


def normalize(value: str) -> str:
    value = value.strip().strip("`").strip()
    return re.sub(r"\s+", " ", value)


def is_meaningful(value: str) -> bool:
    normalized = normalize(value).lower()
    if normalized in PLACEHOLDER_VALUES:
        return False
    if "_tbd_" in normalized:
        return False
    return bool(normalized)


def read_artifact(path: Path) -> Artifact:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        text = None
    return Artifact(path=path, text=text)


def section(text: str, name: str) -> str:
    lines = text.splitlines()
    target = name.strip().lower()
    start: int | None = None
    level = 0

    for index, line in enumerate(lines):
        match = HEADING_RE.match(line.strip())
        if match and match.group("title").strip().lower() == target:
            start = index + 1
            level = len(match.group("marks"))
            break

    if start is None:
        return ""

    collected: list[str] = []
    for line in lines[start:]:
        match = HEADING_RE.match(line.strip())
        if match and len(match.group("marks")) <= level:
            break
        collected.append(line)
    return "\n".join(collected).strip()


def meaningful_lines(block: str) -> list[str]:
    values: list[str] = []
    for raw in block.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("<!--"):
            continue
        stripped = re.sub(r"^[-*+]\s+", "", stripped)
        if is_meaningful(stripped):
            values.append(normalize(stripped))
    return values


def field_values(text: str, label: str) -> list[str]:
    target = label.strip().lower()
    values: list[str] = []
    for line in text.splitlines():
        match = FIELD_RE.match(line)
        if not match:
            continue
        if match.group("label").strip().lower() != target:
            continue
        value = normalize(match.group("value"))
        if is_meaningful(value):
            values.append(value)
    return values


def first_field(text: str, *labels: str) -> str | None:
    for label in labels:
        values = field_values(text, label)
        if values:
            return values[0]
    return None


def recorded_verify_status(verify: Artifact) -> str:
    if not verify.present or verify.text is None:
        return "REVIEW_REQUIRED"
    match = STATUS_RE.search(section(verify.text, "Verify gate") or verify.text)
    if not match:
        return "REVIEW_REQUIRED"
    return match.group(1)


def run_verify_gate(base: str | None, spec: Path, verify: Path) -> RuntimeCheck:
    if base is None:
        return RuntimeCheck(
            status="REVIEW_REQUIRED",
            details=["deterministic verify gate not run; supply --base"],
        )
    if not VERIFY_GATE.is_file():
        return RuntimeCheck(
            status="REVIEW_REQUIRED",
            details=[f"verify gate unavailable: {VERIFY_GATE}"],
        )
    result = subprocess.run(
        [
            sys.executable,
            str(VERIFY_GATE),
            "--base",
            base,
            "--spec",
            str(spec),
            "--verify",
            str(verify),
            "--format",
            "json",
        ],
        cwd=Path.cwd(),
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        detail = result.stderr.strip() or result.stdout.strip() or "no output"
        return RuntimeCheck(
            status="REVIEW_REQUIRED",
            details=[f"verify gate output could not be parsed: {detail}"],
        )
    status = payload.get("status")
    if status not in VALID_STATUSES:
        return RuntimeCheck(
            status="REVIEW_REQUIRED",
            details=["verify gate returned an unknown status"],
        )
    details: list[str] = []
    for key in ("failures", "review_required"):
        value = payload.get(key, [])
        if isinstance(value, list):
            details.extend(str(item) for item in value if str(item).strip())
    changed = payload.get("changed_files", [])
    changed_files = tuple(str(item) for item in changed) if isinstance(changed, list) else ()
    raw_checks = payload.get("checks", [])
    checks: list[str] = []
    if isinstance(raw_checks, list):
        for item in raw_checks:
            if not isinstance(item, dict):
                continue
            name = normalize(str(item.get("name", "check")))
            check_status = normalize(str(item.get("status", "unknown")))
            check_details = normalize(str(item.get("details", "not recorded")))
            checks.append(f"{name}: {check_status} — {check_details}")
    return RuntimeCheck(
        status=status,
        details=details,
        changed_files=changed_files,
        checks=tuple(checks),
    )


def run_handoff_freshness(handoff: Artifact) -> RuntimeCheck | None:
    if not handoff.present:
        return None
    if not HANDOFF_FRESHNESS.is_file():
        return RuntimeCheck(
            status="REVIEW_REQUIRED",
            details=[f"handoff freshness guard unavailable: {HANDOFF_FRESHNESS}"],
        )
    result = subprocess.run(
        [
            sys.executable,
            str(HANDOFF_FRESHNESS),
            "check",
            "--root",
            str(Path.cwd()),
            "--handoff",
            str(handoff.path),
        ],
        cwd=Path.cwd(),
        capture_output=True,
        text=True,
        check=False,
    )
    output = "\n".join(part for part in (result.stdout, result.stderr) if part).strip()
    if "HANDOFF FRESHNESS: PASS" in output:
        status = "PASS"
    elif "HANDOFF FRESHNESS: STALE" in output:
        status = "REVIEW_REQUIRED"
    else:
        status = "REVIEW_REQUIRED"
    details = [
        normalize(line.lstrip("- "))
        for line in output.splitlines()[1:]
        if is_meaningful(line)
    ]
    if "HANDOFF FRESHNESS: STALE" in output:
        details.insert(0, "handoff is STALE; continuation state is advisory only")
    return RuntimeCheck(status=status, details=details)


def overall_status(
    recorded: str,
    gate: RuntimeCheck,
    handoff: RuntimeCheck | None,
) -> str:
    statuses = [recorded, gate.status]
    if handoff is not None:
        statuses.append(handoff.status)
    if "FAIL" in statuses:
        return "FAIL"
    if all(status == "PASS" for status in statuses):
        return "PASS"
    return "REVIEW_REQUIRED"


def command_evidence(verify: Artifact) -> list[dict[str, str]]:
    if not verify.present or verify.text is None:
        return []
    block = section(verify.text, "Command evidence")
    records: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for line in block.splitlines():
        match = FIELD_RE.match(line)
        if not match:
            continue
        label = match.group("label").strip().lower()
        value = normalize(match.group("value"))
        if label == "remaining uncertainty" and value.lower() == "none":
            pass
        elif not is_meaningful(value):
            continue
        if label == "command":
            if current:
                records.append(current)
            current = {"command": value}
        elif current is not None:
            current[label] = value
    if current:
        records.append(current)
    return records


def append_list(lines: list[str], title: str, values: list[str], fallback: str) -> None:
    lines.append(f"### {title}")
    if values:
        lines.extend(f"- {value}" for value in values)
    else:
        lines.append(f"- {fallback}")
    lines.append("")


def render_markdown(
    spec: Artifact,
    verify: Artifact,
    handoff: Artifact,
    gate: RuntimeCheck,
    freshness: RuntimeCheck | None,
    base: str | None,
) -> str:
    recorded = recorded_verify_status(verify)
    overall = overall_status(recorded, gate, freshness)
    lines = [
        "## PR Evidence Summary",
        "",
        "> Generated from workflow artifacts. This renderer compresses recorded",
        "> evidence; it does not establish correctness or upgrade missing, stale,",
        "> failing, or review-required evidence.",
        "",
        "### Evidence state",
        f"- Overall: **{overall}**",
        f"- Recorded verify gate: **{recorded}**",
        f"- Deterministic verify gate: **{gate.status}**"
        + (f" against `{base}`" if base else " (not run)"),
    ]
    if freshness is None:
        lines.append("- Handoff freshness: not included")
    else:
        lines.append(f"- Handoff freshness: **{freshness.status}**")
    lines.append("")

    objective = (
        meaningful_lines(section(spec.text or "", "Objective")) if spec.present else []
    )
    criteria = (
        meaningful_lines(section(spec.text or "", "Acceptance criteria"))
        if spec.present
        else []
    )
    non_goals = (
        meaningful_lines(section(spec.text or "", "Non-goals")) if spec.present else []
    )
    append_list(
        lines,
        "Objective",
        objective,
        "Not established: SPEC objective is missing or incomplete.",
    )
    append_list(
        lines,
        "Acceptance criteria",
        criteria,
        "Not established: acceptance criteria are missing or incomplete.",
    )
    append_list(lines, "Explicit non-goals", non_goals, "None recorded.")

    lines.append("### Verification")
    records = command_evidence(verify)
    if not records:
        lines.append("- Not established: no complete command evidence was recorded.")
    for record in records:
        command = record.get("command", "not recorded")
        exit_code = record.get("exit code", "not recorded")
        interpretation = record.get("interpretation", "not recorded")
        criterion = record.get("acceptance criterion covered", "not recorded")
        uncertainty = record.get("remaining uncertainty", "not recorded")
        lines.append(f"- `{command}` — exit `{exit_code}`; {interpretation}")
        lines.append(f"  - Criterion: {criterion}")
        lines.append(f"  - Remaining uncertainty: {uncertainty}")
    lines.append("")

    verify_text = verify.text or ""
    files = first_field(verify_text, "Files touched", "Changed files")
    tests_changed = first_field(verify_text, "Tests changed")
    protected = first_field(verify_text, "Protected paths touched")
    fixtures = first_field(verify_text, "Fixture/data changed")
    dependencies = first_field(verify_text, "Dependencies changed")
    lines.append("### Diff guard")
    if gate.changed_files:
        lines.append("- Deterministic changed files:")
        lines.extend(f"  - `{path}`" for path in gate.changed_files)
    else:
        lines.append(f"- Files touched (artifact record): {files or 'not recorded'}")
    if gate.checks:
        lines.append("- Deterministic checks:")
        lines.extend(f"  - {check}" for check in gate.checks)
    lines.extend(
        [
            f"- Tests changed (artifact record): {tests_changed or 'not recorded'}",
            f"- Protected paths touched (artifact record): {protected or 'not recorded'}",
            f"- Fixture/data changed (artifact record): {fixtures or 'not recorded'}",
            f"- Dependencies changed (artifact record): {dependencies or 'not recorded'}",
            "",
        ]
    )

    risks: list[str] = []
    review_reason = first_field(verify_text, "Review required because")
    if review_reason:
        risks.append(review_reason)
    remaining = first_field(verify_text, "Remaining unverified risks")
    if remaining:
        risks.append(remaining)
    risks.extend(gate.details)
    if freshness is not None and freshness.status != "PASS":
        risks.extend(freshness.details)
    if overall == "PASS" and not risks:
        risks.append("No unresolved risk was recorded by the supplied checks.")
    elif not risks:
        risks.append("Evidence is incomplete; review the missing status or artifact above.")
    append_list(lines, "Remaining risk", list(dict.fromkeys(risks)), "Not established.")

    if handoff.present and handoff.text is not None:
        next_task = first_field(handoff.text, "Next task")
        if next_task is None:
            next_task_lines = meaningful_lines(
                section(handoff.text, "Next recommended task")
            )
            next_task = next_task_lines[0] if next_task_lines else None
        next_command = first_field(
            handoff.text,
            "Next verification command",
            "Next gate command",
        )
        lines.append("### Continuation")
        if freshness is not None and freshness.status != "PASS":
            lines.append(
                "- Blocked: handoff freshness is not PASS; re-read live state first."
            )
        else:
            lines.append(f"- Next task: {next_task or 'not recorded'}")
            lines.append(f"- Next verification: {next_command or 'not recorded'}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, default=DEFAULT_SPEC)
    parser.add_argument("--verify", type=Path, default=DEFAULT_VERIFY)
    handoff_group = parser.add_mutually_exclusive_group()
    handoff_group.add_argument("--handoff", type=Path, default=DEFAULT_HANDOFF)
    handoff_group.add_argument(
        "--no-handoff",
        action="store_true",
        help="Omit continuation state even when HANDOFF.md exists.",
    )
    parser.add_argument("--base", help="Git base passed to scripts/verify_gate.py")
    parser.add_argument("--output", type=Path, help="Write Markdown to this path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    spec = read_artifact(args.spec)
    verify = read_artifact(args.verify)
    handoff = (
        Artifact(path=args.handoff, text=None)
        if args.no_handoff
        else read_artifact(args.handoff)
    )
    gate = run_verify_gate(args.base, args.spec, args.verify)
    freshness = run_handoff_freshness(handoff)
    markdown = render_markdown(spec, verify, handoff, gate, freshness, args.base)
    if args.output:
        args.output.write_text(markdown, encoding="utf-8")
    else:
        print(markdown, end="")
    status = overall_status(recorded_verify_status(verify), gate, freshness)
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
