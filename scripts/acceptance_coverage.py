#!/usr/bin/env python3
"""Opt-in acceptance-to-evidence coverage for explicitly numbered criteria.

LINKED means there is a recorded evidence reference, not proven correctness.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from verification_evidence import parse_structured_evidence

HEADING = re.compile(r"^ {0,3}(#{1,6})\s+(.+?)\s*$")
BULLET = re.compile(r"^(?:[-*+]|[1-9]\d*[.)])\s+(.+)$")
CRITERION = re.compile(r"^`?(AC-[1-9]\d*)`?\s*:\s*(.+)$")
IDENTIFIER = re.compile(r"^AC-[1-9]\d*$")
PLACEHOLDERS = {"tbd", "_tbd_", "todo", "placeholder"}
SUPPORTED_SOURCES = {"command", "artifact", "manual"}


@dataclass(frozen=True)
class Row:
    criterion: str
    description: str
    checks: tuple[str, ...]
    status: str  # LINKED | MISSING | REVIEW_REQUIRED | FAIL


@dataclass(frozen=True)
class Result:
    active: bool
    status: str  # NOT_APPLICABLE | PASS | REVIEW_REQUIRED | FAIL
    rows: tuple[Row, ...]
    warnings: tuple[str, ...]


def acceptance_bullets(spec: str) -> list[str]:
    """Collect top-level bullets only from the Acceptance criteria section."""
    lines = spec.splitlines()
    begin: int | None = None
    depth = 0
    for index, line in enumerate(lines):
        match = HEADING.match(line)
        if match and match.group(2).strip().lower() == "acceptance criteria":
            begin, depth = index + 1, len(match.group(1))
            break
    if begin is None:
        return []
    bullets: list[str] = []
    for line in lines[begin:]:
        match = HEADING.match(line)
        if match and len(match.group(1)) <= depth:
            break
        bullet = BULLET.match(line)
        if bullet:
            bullets.append(bullet.group(1).strip())
    return bullets


def evaluate(spec: str, verify: str) -> Result:
    """Map AC IDs to valid structured evidence without claiming test sufficiency."""
    bullets = acceptance_bullets(spec)
    parsed = [(text, CRITERION.fullmatch(text)) for text in bullets]
    if not any(match for _, match in parsed):
        return Result(False, "NOT_APPLICABLE", (), ())

    warnings: list[str] = []
    descriptions: dict[str, str] = {}
    for text, match in parsed:
        if match is None:
            warnings.append(f"untagged or malformed acceptance criterion: {text}")
            continue
        criterion, description = match.group(1), match.group(2).strip()
        if criterion in descriptions:
            warnings.append(f"duplicate acceptance criterion ID: {criterion}")
            continue
        if description.lower().strip("`*_ ") in PLACEHOLDERS:
            warnings.append(f"acceptance criterion {criterion} has placeholder content")
        descriptions[criterion] = description

    evidence = parse_structured_evidence(verify)
    if not evidence.present:
        warnings.append("structured verification evidence is missing; legacy prose cannot prove ID coverage")
    elif evidence.errors:
        warnings.append("structured verification evidence is invalid: " + "; ".join(evidence.errors))

    links: dict[str, list[dict[str, object]]] = {key: [] for key in descriptions}
    if evidence.present and not evidence.errors:
        for record in evidence.checks:
            raw = record.get("acceptance_criterion")
            if raw is None or not str(raw).strip():
                continue
            reference = str(raw).strip()
            if not IDENTIFIER.fullmatch(reference):
                warnings.append(f"check {record['check']} has non-ID acceptance reference: {reference}")
            elif reference not in links:
                warnings.append(f"check {record['check']} references unknown criterion: {reference}")
            else:
                links[reference].append(record)

    rows: list[Row] = []
    for identifier, description in descriptions.items():
        records = links[identifier]
        checks = tuple(str(record["check"]) for record in records)
        if any(record["status"] == "FAIL" for record in records):
            row_status = "FAIL"
        elif any(record["status"] == "REVIEW_REQUIRED" for record in records):
            row_status = "REVIEW_REQUIRED"
        elif any(
            record["status"] == "PASS"
            and record["evidence_source"] in SUPPORTED_SOURCES
            for record in records
        ):
            row_status = "LINKED"
        elif records:
            row_status = "REVIEW_REQUIRED"  # inferred PASS is not a recorded proof
        else:
            row_status = "MISSING"
        rows.append(Row(identifier, description, checks, row_status))

    if any(row.status == "FAIL" for row in rows):
        status = "FAIL"
    elif warnings or any(row.status != "LINKED" for row in rows):
        status = "REVIEW_REQUIRED"
    else:
        status = "PASS"
    return Result(True, status, tuple(rows), tuple(warnings))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, default=Path("SPEC.md"))
    parser.add_argument("--verify", type=Path, default=Path("VERIFY.md"))
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)
    try:
        spec = args.spec.read_text(encoding="utf-8")
        verify = args.verify.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        parser.exit(2, f"coverage input error: {exc}\n")
    result = evaluate(spec, verify)
    if args.format == "json":
        print(json.dumps(asdict(result), indent=2))
    else:
        print(f"ACCEPTANCE COVERAGE: {result.status}")
        for row in result.rows:
            print(f"- {row.criterion}: {row.status}; checks: {', '.join(row.checks) or 'none'}")
        for warning in result.warnings:
            print(f"- REVIEW_REQUIRED: {warning}")
        if result.active:
            print("LINKED means recorded supporting evidence, not verified correctness.")
    return {"PASS": 0, "NOT_APPLICABLE": 0, "REVIEW_REQUIRED": 3, "FAIL": 1}[result.status]


if __name__ == "__main__":
    raise SystemExit(main())
