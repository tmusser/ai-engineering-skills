#!/usr/bin/env python3
"""Parse and validate machine-readable verification evidence embedded in VERIFY.md."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any


VALID_STATUSES = {"PASS", "FAIL", "REVIEW_REQUIRED"}
VALID_SOURCES = {"command", "artifact", "manual", "inferred"}
HEADING_RE = re.compile(r"^\s{0,3}(?P<marks>#{1,6})\s+(?P<title>.+?)\s*$")
JSON_FENCE_RE = re.compile(r"\x60\x60\x60json\s*\n(?P<body>.*?)\n\x60\x60\x60", re.DOTALL | re.IGNORECASE)
SECTION_NAMES = {"structured verification evidence", "machine-readable evidence"}


@dataclass(frozen=True)
class StructuredEvidence:
    """Validated representation of the optional structured evidence block."""

    present: bool
    checks: tuple[dict[str, Any], ...]
    errors: tuple[str, ...]


def _section(text: str) -> str | None:
    lines = text.splitlines()
    start: int | None = None
    level = 0
    for index, line in enumerate(lines):
        match = HEADING_RE.match(line)
        if not match:
            continue
        title = match.group("title").strip().lower()
        if title in SECTION_NAMES:
            start = index + 1
            level = len(match.group("marks"))
            break
    if start is None:
        return None

    collected: list[str] = []
    for line in lines[start:]:
        match = HEADING_RE.match(line)
        if match and len(match.group("marks")) <= level:
            break
        collected.append(line)
    return "\n".join(collected)


def _meaningful_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip()) and value.strip().lower() not in {
        "_tbd_",
        "tbd",
        "none",
        "n/a",
    }


def _validate_check(index: int, raw: Any) -> list[str]:
    prefix = f"check[{index}]"
    if not isinstance(raw, dict):
        return [f"{prefix} must be an object"]

    errors: list[str] = []
    for field in ("check", "evidence_source", "status", "evidence"):
        if not _meaningful_string(raw.get(field)):
            errors.append(f"{prefix}.{field} must be a non-placeholder string")

    source = raw.get("evidence_source")
    if isinstance(source, str) and source not in VALID_SOURCES:
        errors.append(
            f"{prefix}.evidence_source must be one of: {', '.join(sorted(VALID_SOURCES))}"
        )

    status = raw.get("status")
    if isinstance(status, str) and status not in VALID_STATUSES:
        errors.append(
            f"{prefix}.status must be one of: {', '.join(sorted(VALID_STATUSES))}"
        )

    if "command" not in raw:
        errors.append(f"{prefix}.command is required (use null when not command-backed)")
    elif raw["command"] is not None and not _meaningful_string(raw["command"]):
        errors.append(f"{prefix}.command must be a string or null")

    if "exit_code" not in raw:
        errors.append(f"{prefix}.exit_code is required (use null when not command-backed)")
    elif raw["exit_code"] is not None and (
        isinstance(raw["exit_code"], bool) or not isinstance(raw["exit_code"], int)
    ):
        errors.append(f"{prefix}.exit_code must be an integer or null")

    if source == "command":
        if not _meaningful_string(raw.get("command")):
            errors.append(f"{prefix} command evidence requires command")
        if isinstance(raw.get("exit_code"), bool) or not isinstance(raw.get("exit_code"), int):
            errors.append(f"{prefix} command evidence requires integer exit_code")
        elif status == "PASS" and raw["exit_code"] != 0:
            errors.append(f"{prefix} PASS command evidence must have exit_code 0")
    elif raw.get("exit_code") is not None and raw.get("command") is None:
        errors.append(f"{prefix}.exit_code requires a command")

    recorded_at = raw.get("recorded_at")
    commit = raw.get("commit")
    if not _meaningful_string(recorded_at) and not _meaningful_string(commit):
        errors.append(f"{prefix} requires recorded_at or commit provenance")
    if recorded_at is not None and not _meaningful_string(recorded_at):
        errors.append(f"{prefix}.recorded_at must be a non-placeholder string when present")
    if commit is not None and not _meaningful_string(commit):
        errors.append(f"{prefix}.commit must be a non-placeholder string when present")

    for optional in ("acceptance_criterion", "remaining_uncertainty"):
        if optional in raw and raw[optional] is not None and not isinstance(raw[optional], str):
            errors.append(f"{prefix}.{optional} must be a string or null")

    allowed = {
        "check",
        "command",
        "exit_code",
        "evidence_source",
        "status",
        "evidence",
        "recorded_at",
        "commit",
        "acceptance_criterion",
        "remaining_uncertainty",
    }
    unexpected = sorted(set(raw) - allowed)
    if unexpected:
        errors.append(f"{prefix} has unknown field(s): {', '.join(unexpected)}")

    return errors


def parse_structured_evidence(text: str) -> StructuredEvidence:
    """Parse the optional structured evidence section without affecting legacy artifacts."""
    block = _section(text)
    if block is None:
        return StructuredEvidence(present=False, checks=(), errors=())

    matches = list(JSON_FENCE_RE.finditer(block))
    if len(matches) != 1:
        return StructuredEvidence(
            present=True,
            checks=(),
            errors=("structured evidence section must contain exactly one fenced json block",),
        )

    try:
        payload = json.loads(matches[0].group("body"))
    except json.JSONDecodeError as exc:
        return StructuredEvidence(
            present=True,
            checks=(),
            errors=(f"structured evidence JSON is invalid: {exc.msg}",),
        )

    if not isinstance(payload, dict):
        return StructuredEvidence(
            present=True,
            checks=(),
            errors=("structured evidence JSON root must be an object",),
        )

    errors: list[str] = []
    if payload.get("schema_version") != 1:
        errors.append("schema_version must be 1")

    raw_checks = payload.get("checks")
    if not isinstance(raw_checks, list) or not raw_checks:
        errors.append("checks must be a non-empty array")
        raw_checks = []

    ids: set[str] = set()
    for index, raw in enumerate(raw_checks):
        errors.extend(_validate_check(index, raw))
        if isinstance(raw, dict):
            check_id = raw.get("check")
            if _meaningful_string(check_id):
                normalized = check_id.strip()
                if normalized in ids:
                    errors.append(f"duplicate check id: {normalized}")
                ids.add(normalized)

    unexpected_root = sorted(set(payload) - {"schema_version", "checks"})
    if unexpected_root:
        errors.append("structured evidence root has unknown field(s): " + ", ".join(unexpected_root))

    checks = tuple(raw for raw in raw_checks if isinstance(raw, dict))
    return StructuredEvidence(
        present=True,
        checks=checks,
        errors=tuple(errors),
    )
