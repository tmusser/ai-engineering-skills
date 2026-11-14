#!/usr/bin/env python3
"""Read-only hygiene check for optional durable DECISIONS.md entries.

Reports structural and supersession inconsistencies, not decision correctness,
authorization, evidence freshness, or whether an agent should have decided.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

HEADER = re.compile(r"^## (D[1-9]\d*)\s*[:—-]\s*(\S.*)$")
FIELD = re.compile(r"^- ([A-Za-z][A-Za-z ]*):\s*(.*)$")
FENCE = re.compile(r"^\s{0,3}(\x60{3,}|~{3,})")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DECISION_ID = re.compile(r"^D[1-9]\d*$")
REQUIRED_FIELDS = (
    "Status", "Date", "Authority", "Why", "Alternatives",
    "Evidence", "Consequences", "Revisit if", "Supersedes",
)
PLACEHOLDERS = {"", "-", "_tbd_", "tbd", "todo", "n/a", "unknown", "pending"}


@dataclass(frozen=True)
class Entry:
    id: str
    title: str
    line: int
    fields: dict[str, str]


@dataclass(frozen=True)
class Result:
    status: str
    decisions: tuple[dict[str, str], ...]
    review_required: tuple[str, ...]


def visible_lines(text: str):
    """Ignore fenced examples and HTML comments; yield source line numbers."""
    fence: tuple[str, int] | None = None
    comment = False
    for number, line in enumerate(text.splitlines(), 1):
        if comment:
            if "-->" in line:
                comment = False
            continue
        stripped = line.strip()
        if stripped.startswith("<!--"):
            if "-->" not in stripped:
                comment = True
            continue
        marker = FENCE.match(line)
        if fence is not None:
            if marker:
                run = marker.group(1)
                if run[0] == fence[0] and len(run) >= fence[1] and not line[marker.end(1):].strip():
                    fence = None
            continue
        if marker:
            run = marker.group(1)
            fence = (run[0], len(run))
            continue
        yield number, line


def read_entries(text: str) -> tuple[list[Entry], list[str]]:
    entries: list[Entry] = []
    issues: list[str] = []
    current_id: str | None = None
    current_title = ""
    current_line = 0
    fields: dict[str, str] = {}

    def finish():
        if current_id is not None:
            entries.append(Entry(current_id, current_title, current_line, fields.copy()))

    for number, line in visible_lines(text):
        if line.startswith("## "):
            finish()
            fields = {}
            match = HEADER.fullmatch(line)
            if match:
                current_id, current_title = match.group(1), match.group(2).strip()
                current_line = number
            else:
                current_id = None
                issues.append(f"line {number}: decision heading must use '## D1: Short outcome'")
            continue
        if current_id is None:
            continue
        if not line.strip() or line.startswith("### "):
            continue
        match = FIELD.fullmatch(line)
        if not match:
            issues.append(f"{current_id} line {number}: unstructured content (use one-line '- Field: value')")
            continue
        key, value = match.group(1), match.group(2).strip()
        if key not in REQUIRED_FIELDS:
            issues.append(f"{current_id} line {number}: unexpected field {key!r}")
        elif key in fields:
            issues.append(f"{current_id} line {number}: duplicate field {key!r}")
        else:
            fields[key] = value
    finish()
    return entries, issues


def meaningful(value: str) -> bool:
    candidate = value.strip()
    return candidate.lower() not in PLACEHOLDERS and "_tbd_" not in candidate.lower()


def evaluate(text: str | None) -> Result:
    """Validate one optional ledger with fail-closed review semantics."""
    if text is None:
        return Result("NOT_APPLICABLE", (), ())
    entries, issues = read_entries(text)
    if not entries and not issues:
        return Result("NOT_APPLICABLE", (), ())

    seen: dict[str, Entry] = {}
    predecessors: dict[str, list[str]] = {}
    dates: dict[str, date] = {}
    for entry in entries:
        if entry.id in seen:
            issues.append(f"{entry.id} line {entry.line}: duplicate decision ID")
            continue
        seen[entry.id] = entry
        for field in REQUIRED_FIELDS:
            value = entry.fields.get(field)
            if value is None:
                issues.append(f"{entry.id}: missing {field}")
            elif field != "Supersedes" and not meaningful(value):
                issues.append(f"{entry.id}: missing or placeholder {field}")

        status = entry.fields.get("Status", "")
        if status not in {"ACTIVE", "SUPERSEDED"}:
            issues.append(f"{entry.id}: Status must be ACTIVE or SUPERSEDED")

        raw_date = entry.fields.get("Date", "")
        if not DATE.fullmatch(raw_date):
            issues.append(f"{entry.id}: Date must be YYYY-MM-DD")
        else:
            try:
                dates[entry.id] = date.fromisoformat(raw_date)
            except ValueError:
                issues.append(f"{entry.id}: invalid calendar Date {raw_date}")

        prior = entry.fields.get("Supersedes", "")
        if prior == "none":
            continue
        if not DECISION_ID.fullmatch(prior):
            issues.append(f"{entry.id}: Supersedes must be one earlier D-ID or 'none'")
            continue
        if prior not in seen or prior == entry.id:
            issues.append(f"{entry.id}: superseded decision {prior} must appear earlier in the ledger")
            continue
        predecessors.setdefault(prior, []).append(entry.id)
        if prior in dates and entry.id in dates and dates[entry.id] < dates[prior]:
            issues.append(f"{entry.id}: Date predates superseded decision {prior}")

    for entry in entries:
        if seen.get(entry.id) is not entry:
            continue
        successors = predecessors.get(entry.id, [])
        status = entry.fields.get("Status")
        if len(successors) > 1:
            issues.append(f"{entry.id}: multiple successors: {', '.join(successors)}")
        if status == "ACTIVE" and successors:
            issues.append(f"{entry.id}: ACTIVE but superseded by {', '.join(successors)}")
        if status == "SUPERSEDED" and len(successors) != 1:
            issues.append(f"{entry.id}: SUPERSEDED must have exactly one later successor")

    rows = tuple({
        "id": entry.id,
        "title": entry.title,
        "status": entry.fields.get("Status", "UNKNOWN"),
        "supersedes": entry.fields.get("Supersedes", "UNKNOWN"),
    } for entry in entries)
    return Result("REVIEW_REQUIRED" if issues else "PASS", rows, tuple(issues))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decisions", type=Path, default=Path("DECISIONS.md"))
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)
    if not args.decisions.exists():
        result = evaluate(None)
    else:
        try:
            if not args.decisions.is_file():
                raise OSError("not a regular file")
            result = evaluate(args.decisions.read_text(encoding="utf-8"))
        except (OSError, UnicodeError) as exc:
            print(f"decision ledger input error: {exc}", file=sys.stderr)
            return 2

    if args.format == "json":
        print(json.dumps(asdict(result), indent=2))
    else:
        print(f"DECISION LEDGER: {result.status}")
        for entry in result.decisions:
            print(f"- {entry['id']} [{entry['status']}]: {entry['title']}")
        for item in result.review_required:
            print(f"- REVIEW_REQUIRED: {item}")
        print("Structural check only; authority, evidence, and semantics are not independently verified.")
    return 0 if result.status in {"PASS", "NOT_APPLICABLE"} else 3


if __name__ == "__main__":
    raise SystemExit(main())
