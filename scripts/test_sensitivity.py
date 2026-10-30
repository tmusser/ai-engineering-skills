#!/usr/bin/env python3
"""Validate optional test-sensitivity fault-injection evidence."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

STATUS_PASS = "PASS"
STATUS_REVIEW = "REVIEW_REQUIRED"
STATUS_NA = "NOT_APPLICABLE"

HEADING_RE = re.compile(r"^\s{0,3}(?P<marks>#{1,6})\s+(?P<title>.+?)\s*$")
FIELD_RE = re.compile(
    r"^\s*[-*+]?\s*(?P<label>[^:]+):\s*(?P<value>.*?)\s*$",
    re.IGNORECASE,
)
REQUIREMENT_RE = re.compile(
    r"(?im)^\s*Test\s+sensitivity\s+requirement\s*:\s*(REQUIRED|NOT_APPLICABLE)\s*$"
)
PLACEHOLDERS = {
    "",
    "-",
    "_tbd_",
    "tbd",
    "none",
    "n/a",
    "required | not_applicable",
    "yes/no",
}


@dataclass(frozen=True)
class Record:
    """One declared sensitivity probe and its verification evidence."""

    sensitivity_id: str
    protected_behavior: str
    test_command: str
    fault_model: str
    fault_injected: str | None
    mutated_command: str | None
    mutated_exit_code: int | None
    expected_failure_observed: bool | None
    failure_evidence: str | None
    restored_exit_code: int | None
    restoration_evidence: str | None


@dataclass(frozen=True)
class Result:
    """Test-sensitivity contract result."""

    active: bool
    status: str
    records: tuple[Record, ...]
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
    value = value.strip().strip(chr(96)).strip()
    return re.sub(r"\s+", " ", value)


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
        if label == "sensitivity id":
            if current is not None:
                records.append(current)
            current = {"sensitivity id": value}
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


def parse_yes_no(value: str | None) -> bool | None:
    if not meaningful(value):
        return None
    lowered = normalize(value or "").lower()
    if lowered == "yes":
        return True
    if lowered == "no":
        return False
    return None


def evaluate(spec_text: str | None, verify_text: str | None) -> Result:
    """Evaluate the optional SPEC-to-VERIFY test-sensitivity contract."""
    if spec_text is None:
        return Result(False, STATUS_NA, (), ())

    gate_lines = section_lines(spec_text, ("test sensitivity gate",))
    if not gate_lines:
        return Result(False, STATUS_NA, (), ())

    gate_text = "\n".join(gate_lines)
    requirement = REQUIREMENT_RE.search(gate_text)
    if requirement is None:
        return Result(
            True,
            STATUS_REVIEW,
            (),
            ("test sensitivity requirement is missing or unresolved",),
        )
    if requirement.group(1) == "NOT_APPLICABLE":
        return Result(False, STATUS_NA, (), ())

    problems: list[str] = []
    spec_records = parse_records(spec_text, ("test sensitivity gate",))
    if not spec_records:
        return Result(
            True,
            STATUS_REVIEW,
            (),
            ("test sensitivity is REQUIRED but no sensitivity probe is declared",),
        )

    spec_by_id: dict[str, dict[str, str]] = {}
    for record in spec_records:
        sensitivity_id = normalize(record.get("sensitivity id", ""))
        if not meaningful(sensitivity_id):
            problems.append("sensitivity probe has missing Sensitivity ID")
            continue
        if sensitivity_id in spec_by_id:
            problems.append(f"duplicate SPEC Sensitivity ID: {sensitivity_id}")
            continue
        spec_by_id[sensitivity_id] = record
        missing = [
            field
            for field in ("protected behavior", "test command", "fault model")
            if not meaningful(record.get(field))
        ]
        if missing:
            problems.append(
                f"{sensitivity_id} missing SPEC fields: {', '.join(missing)}"
            )

    verify_by_id: dict[str, dict[str, str]] = {}
    if verify_text is None:
        problems.append("test sensitivity is REQUIRED but VERIFY.md evidence is unavailable")
    else:
        verify_records = parse_records(
            verify_text,
            ("test sensitivity evidence", "test sensitivity"),
        )
        for record in verify_records:
            sensitivity_id = normalize(record.get("sensitivity id", ""))
            if not meaningful(sensitivity_id):
                problems.append("verification sensitivity record has missing Sensitivity ID")
                continue
            if sensitivity_id in verify_by_id:
                problems.append(f"duplicate verification Sensitivity ID: {sensitivity_id}")
                continue
            verify_by_id[sensitivity_id] = record

    unexpected = sorted(set(verify_by_id) - set(spec_by_id))
    if unexpected:
        problems.append(
            "verification contains undeclared Sensitivity ID(s): " + ", ".join(unexpected)
        )

    output_records: list[Record] = []
    for sensitivity_id, declared in spec_by_id.items():
        evidence = verify_by_id.get(sensitivity_id)
        protected_behavior = normalize(declared.get("protected behavior", ""))
        test_command = normalize(declared.get("test command", ""))
        fault_model = normalize(declared.get("fault model", ""))

        if evidence is None:
            problems.append(f"{sensitivity_id} missing test-sensitivity evidence")
            output_records.append(
                Record(
                    sensitivity_id,
                    protected_behavior,
                    test_command,
                    fault_model,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                )
            )
            continue

        missing = [
            field
            for field in (
                "fault injected",
                "mutated command",
                "mutated exit code",
                "expected failure observed",
                "failure evidence",
                "restored exit code",
                "restoration evidence",
            )
            if not meaningful(evidence.get(field))
        ]
        if missing:
            problems.append(
                f"{sensitivity_id} missing verification fields: {', '.join(missing)}"
            )

        fault_injected = (
            normalize(evidence.get("fault injected", ""))
            if meaningful(evidence.get("fault injected"))
            else None
        )
        mutated_command = (
            normalize(evidence.get("mutated command", ""))
            if meaningful(evidence.get("mutated command"))
            else None
        )
        mutated_exit = parse_int(evidence.get("mutated exit code"))
        expected_failure = parse_yes_no(evidence.get("expected failure observed"))
        failure_evidence = (
            normalize(evidence.get("failure evidence", ""))
            if meaningful(evidence.get("failure evidence"))
            else None
        )
        restored_exit = parse_int(evidence.get("restored exit code"))
        restoration_evidence = (
            normalize(evidence.get("restoration evidence", ""))
            if meaningful(evidence.get("restoration evidence"))
            else None
        )

        if mutated_command is not None and mutated_command != test_command:
            problems.append(
                f"{sensitivity_id} mutated command does not match declared Test command"
            )
        if meaningful(evidence.get("mutated exit code")) and mutated_exit is None:
            problems.append(f"{sensitivity_id} Mutated exit code is not an integer")
        elif mutated_exit == 0:
            problems.append(
                f"{sensitivity_id} injected fault survived the targeted test"
            )
        if expected_failure is None and meaningful(evidence.get("expected failure observed")):
            problems.append(
                f"{sensitivity_id} Expected failure observed must be yes or no"
            )
        elif expected_failure is False:
            problems.append(
                f"{sensitivity_id} test failed, but not for the expected protected behavior"
            )
        if meaningful(evidence.get("restored exit code")) and restored_exit is None:
            problems.append(f"{sensitivity_id} Restored exit code is not an integer")
        elif restored_exit not in {None, 0}:
            problems.append(
                f"{sensitivity_id} targeted test did not return to PASS after restoration"
            )

        output_records.append(
            Record(
                sensitivity_id,
                protected_behavior,
                test_command,
                fault_model,
                fault_injected,
                mutated_command,
                mutated_exit,
                expected_failure,
                failure_evidence,
                restored_exit,
                restoration_evidence,
            )
        )

    status = STATUS_REVIEW if problems else STATUS_PASS
    return Result(True, status, tuple(output_records), tuple(problems))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, default=Path("SPEC.md"))
    parser.add_argument("--verify", type=Path, default=Path("VERIFY.md"))
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    spec_text = args.spec.read_text(encoding="utf-8") if args.spec.is_file() else None
    verify_text = args.verify.read_text(encoding="utf-8") if args.verify.is_file() else None
    result = evaluate(spec_text, verify_text)

    if args.format == "json":
        print(json.dumps(asdict(result), indent=2, sort_keys=True))
    else:
        print(f"TEST SENSITIVITY: {result.status}")
        if result.status == STATUS_PASS:
            print(f"- {len(result.records)} required sensitivity probe(s) killed and restored")
        elif result.status == STATUS_NA:
            print("- test sensitivity contract is not active")
        for item in result.review_required:
            print(f"- REVIEW_REQUIRED: {item}")

    return 0 if result.status in {STATUS_PASS, STATUS_NA} else 2


if __name__ == "__main__":
    raise SystemExit(main())
