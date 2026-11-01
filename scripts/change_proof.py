#!/usr/bin/env python3
"""Validate optional baseline -> change -> proof evidence."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

STATUS_PASS = "PASS"
STATUS_FAIL = "FAIL"
STATUS_REVIEW = "REVIEW_REQUIRED"
STATUS_NA = "NOT_APPLICABLE"

HEADING_RE = re.compile(r"^\s{0,3}(?P<marks>#{1,6})\s+(?P<title>.+?)\s*$")
FIELD_RE = re.compile(
    r"^\s*[-*+]?\s*(?P<label>[^:]+):\s*(?P<value>.*?)\s*$",
    re.IGNORECASE,
)
REQUIREMENT_RE = re.compile(
    r"(?im)^\s*Change\s+proof\s+requirement\s*:\s*(REQUIRED|NOT_APPLICABLE)\s*$"
)
PLACEHOLDERS = {
    "",
    "-",
    "_tbd_",
    "tbd",
    "none",
    "n/a",
    "required | not_applicable",
    "pass | fail | review_required",
}


@dataclass(frozen=True)
class Record:
    """One declared before/after proof record."""

    change_id: str
    baseline_commit: str
    baseline_command: str
    baseline_exit_code: int | None
    baseline_evidence: str
    expected_delta: str
    proof_command: str | None
    proof_exit_code: int | None
    delta_result: str | None
    proof_evidence: str | None


@dataclass(frozen=True)
class Result:
    """Change-proof contract result."""

    active: bool
    status: str
    records: tuple[Record, ...]
    failures: tuple[str, ...]
    review_required: tuple[str, ...]


def normalize_heading(line: str) -> tuple[int, str] | None:
    match = HEADING_RE.match(line)
    if not match:
        return None
    title = re.sub(r"[*_]", "", match.group("title").strip().lower())
    title = re.sub(r"[^a-z0-9\s-]", " ", title)
    title = re.sub(r"\s+", " ", title).strip()
    return len(match.group("marks")), title


def section_lines(text: str, names: tuple[str, ...]) -> list[str]:
    lines = text.splitlines()
    wanted = {name.lower() for name in names}
    start: int | None = None
    level = 0
    for index, line in enumerate(lines):
        heading = normalize_heading(line)
        if heading and heading[1] in wanted:
            start = index + 1
            level = heading[0]
            break
    if start is None:
        return []

    collected: list[str] = []
    for line in lines[start:]:
        heading = normalize_heading(line)
        if heading and heading[0] <= level:
            break
        collected.append(line)
    return collected


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().strip(chr(96)).strip())


def meaningful(value: str | None) -> bool:
    if value is None:
        return False
    raw = value.strip()
    if len(raw) > 2 and raw.startswith("_") and raw.endswith("_"):
        return False
    return normalize(value).lower() not in PLACEHOLDERS


def parse_records(text: str, headings: tuple[str, ...]) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for line in section_lines(text, headings):
        match = FIELD_RE.match(line)
        if not match:
            continue
        label = normalize(match.group("label")).lower()
        value = match.group("value").strip()
        if label == "change id":
            if current is not None:
                records.append(current)
            current = {"change id": value}
        elif current is not None:
            current[label] = value
    if current is not None:
        records.append(current)
    return records


def parse_int(value: str | None) -> int | None:
    if not meaningful(value):
        return None
    try:
        return int(normalize(value or ""))
    except ValueError:
        return None


def commits_match(recorded: str, expected: str) -> bool:
    """Allow normal short-SHA notation while rejecting unrelated commits."""
    left = normalize(recorded).lower()
    right = normalize(expected).lower()
    if len(left) < 7 or len(right) < 7:
        return left == right
    return left.startswith(right) or right.startswith(left)


def resolve_commit(root: Path, ref: str) -> tuple[str | None, str | None]:
    try:
        process = subprocess.run(
            ["git", "rev-parse", ref],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = exc.stderr.strip() if isinstance(exc, subprocess.CalledProcessError) else str(exc)
        return None, f"unable to resolve verification base {ref}: {detail}".rstrip(": ")
    return process.stdout.strip(), None


def evaluate(
    spec_text: str | None,
    verify_text: str | None,
    *,
    expected_base_commit: str | None = None,
) -> Result:
    """Evaluate the optional SPEC-to-VERIFY change-proof contract."""
    if spec_text is None:
        return Result(False, STATUS_NA, (), (), ())

    headings = ("change proof gate", "change proof gate optional")
    gate_lines = section_lines(spec_text, headings)
    if not gate_lines:
        return Result(False, STATUS_NA, (), (), ())

    requirement = REQUIREMENT_RE.search("\n".join(gate_lines))
    if requirement is None:
        return Result(
            True,
            STATUS_REVIEW,
            (),
            (),
            ("change proof requirement is missing or unresolved",),
        )
    if requirement.group(1) == "NOT_APPLICABLE":
        return Result(False, STATUS_NA, (), (), ())

    failures: list[str] = []
    reviews: list[str] = []
    spec_records = parse_records(spec_text, headings)
    if not spec_records:
        return Result(
            True,
            STATUS_REVIEW,
            (),
            (),
            ("change proof is REQUIRED but no baseline record is declared",),
        )

    spec_by_id: dict[str, dict[str, str]] = {}
    for record in spec_records:
        change_id = normalize(record.get("change id", ""))
        if not meaningful(change_id):
            reviews.append("baseline record has missing Change ID")
            continue
        if change_id in spec_by_id:
            reviews.append(f"duplicate SPEC Change ID: {change_id}")
            continue
        spec_by_id[change_id] = record
        missing = [
            field
            for field in (
                "baseline commit",
                "baseline command",
                "baseline exit code",
                "baseline evidence",
                "expected delta",
            )
            if not meaningful(record.get(field))
        ]
        if missing:
            reviews.append(f"{change_id} missing baseline fields: {', '.join(missing)}")
        if meaningful(record.get("baseline exit code")) and parse_int(record.get("baseline exit code")) is None:
            reviews.append(f"{change_id} Baseline exit code is not an integer")
        baseline_commit = normalize(record.get("baseline commit", ""))
        if expected_base_commit and meaningful(baseline_commit):
            if not commits_match(baseline_commit, expected_base_commit):
                reviews.append(
                    f"{change_id} baseline commit {baseline_commit} does not match "
                    f"verification base {expected_base_commit}"
                )

    verify_by_id: dict[str, dict[str, str]] = {}
    if verify_text is None:
        reviews.append("change proof is REQUIRED but VERIFY.md evidence is unavailable")
    else:
        for record in parse_records(
            verify_text,
            ("change proof evidence", "change proof"),
        ):
            change_id = normalize(record.get("change id", ""))
            if not meaningful(change_id):
                reviews.append("verification change-proof record has missing Change ID")
                continue
            if change_id in verify_by_id:
                reviews.append(f"duplicate verification Change ID: {change_id}")
                continue
            verify_by_id[change_id] = record

    unexpected = sorted(set(verify_by_id) - set(spec_by_id))
    if unexpected:
        reviews.append(
            "verification contains undeclared Change ID(s): " + ", ".join(unexpected)
        )

    output: list[Record] = []
    for change_id, declared in spec_by_id.items():
        baseline_commit = normalize(declared.get("baseline commit", ""))
        baseline_command = normalize(declared.get("baseline command", ""))
        baseline_exit = parse_int(declared.get("baseline exit code"))
        baseline_evidence = normalize(declared.get("baseline evidence", ""))
        expected_delta = normalize(declared.get("expected delta", ""))

        evidence = verify_by_id.get(change_id)
        if evidence is None:
            reviews.append(f"{change_id} missing change-proof evidence")
            output.append(
                Record(
                    change_id,
                    baseline_commit,
                    baseline_command,
                    baseline_exit,
                    baseline_evidence,
                    expected_delta,
                    None,
                    None,
                    None,
                    None,
                )
            )
            continue

        missing = [
            field
            for field in ("proof command", "proof exit code", "delta result", "proof evidence")
            if not meaningful(evidence.get(field))
        ]
        if missing:
            reviews.append(f"{change_id} missing proof fields: {', '.join(missing)}")

        proof_command = (
            normalize(evidence.get("proof command", ""))
            if meaningful(evidence.get("proof command"))
            else None
        )
        proof_exit = parse_int(evidence.get("proof exit code"))
        delta_result = (
            normalize(evidence.get("delta result", "")).upper()
            if meaningful(evidence.get("delta result"))
            else None
        )
        proof_evidence = (
            normalize(evidence.get("proof evidence", ""))
            if meaningful(evidence.get("proof evidence"))
            else None
        )

        if proof_command is not None and proof_command != baseline_command:
            reviews.append(
                f"{change_id} proof command does not match baseline command"
            )
        if meaningful(evidence.get("proof exit code")) and proof_exit is None:
            reviews.append(f"{change_id} Proof exit code is not an integer")

        if delta_result == STATUS_FAIL:
            failures.append(f"{change_id} expected delta was not proven")
        elif delta_result == STATUS_REVIEW:
            reviews.append(f"{change_id} delta result is REVIEW_REQUIRED")
        elif delta_result == STATUS_PASS:
            if proof_exit not in {None, 0}:
                reviews.append(
                    f"{change_id} claims PASS but proof command exited {proof_exit}"
                )
        elif delta_result is not None:
            reviews.append(f"{change_id} has invalid Delta result: {delta_result}")

        output.append(
            Record(
                change_id,
                baseline_commit,
                baseline_command,
                baseline_exit,
                baseline_evidence,
                expected_delta,
                proof_command,
                proof_exit,
                delta_result,
                proof_evidence,
            )
        )

    status = STATUS_FAIL if failures else STATUS_REVIEW if reviews else STATUS_PASS
    return Result(True, status, tuple(output), tuple(failures), tuple(reviews))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--spec", type=Path, default=Path("SPEC.md"))
    parser.add_argument("--verify", type=Path, default=Path("VERIFY.md"))
    parser.add_argument(
        "--base",
        help="Optional git ref that the recorded baseline commit must match.",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.root.expanduser().resolve()
    spec_path = args.spec if args.spec.is_absolute() else root / args.spec
    verify_path = args.verify if args.verify.is_absolute() else root / args.verify
    spec_text = spec_path.read_text(encoding="utf-8") if spec_path.is_file() else None
    verify_text = verify_path.read_text(encoding="utf-8") if verify_path.is_file() else None

    expected_base = None
    if args.base:
        expected_base, error = resolve_commit(root, args.base)
        if error:
            result = Result(True, STATUS_REVIEW, (), (), (error,))
        else:
            result = evaluate(
                spec_text,
                verify_text,
                expected_base_commit=expected_base,
            )
    else:
        result = evaluate(spec_text, verify_text)

    if args.format == "json":
        print(json.dumps(asdict(result), indent=2, sort_keys=True))
    else:
        print(f"CHANGE PROOF: {result.status}")
        if result.status == STATUS_PASS:
            print(f"- {len(result.records)} required change proof(s) established")
        elif result.status == STATUS_NA:
            print("- change-proof contract is not active")
        for item in result.failures:
            print(f"- FAIL: {item}")
        for item in result.review_required:
            print(f"- REVIEW_REQUIRED: {item}")

    return {
        STATUS_PASS: 0,
        STATUS_NA: 0,
        STATUS_FAIL: 1,
        STATUS_REVIEW: 2,
    }[result.status]


if __name__ == "__main__":
    raise SystemExit(main())
