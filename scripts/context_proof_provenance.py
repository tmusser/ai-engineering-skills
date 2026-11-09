#!/usr/bin/env python3
"""Check exact proof commands against source-verified structured VERIFY evidence.

A recorded PASS establishes a claim in the selected verification artifact, not
independent execution, test quality, or workspace freshness.
"""

from __future__ import annotations

from pathlib import Path

from context_sufficiency import PACKET_MARKER, safe_source, verified_excerpts
from verification_evidence import parse_structured_evidence


def check_recorded_proofs(
    payloads: list[tuple[str, str]],
    root: Path,
    verification_source: str,
    commands: list[str],
) -> tuple[list[dict[str, object]], list[str]]:
    """Return recorded PASS matches and warnings from the selected live source.

    Never treat stdin, loose mentions, metadata tables or unrelated files as
    structured verification evidence. A packet excerpt must match the current
    source bytes through the existing hash/range validator.
    """
    path = safe_source(root, verification_source)
    selected: list[str] = []
    warnings: list[str] = []

    for label, contents in payloads:
        if contents.startswith(PACKET_MARKER):
            excerpts, _packet_warnings = verified_excerpts(contents, root)
            selected.extend(excerpts.get(verification_source, []))
        elif label != "<stdin>" and Path(label).resolve() == path:
            try:
                live = path.read_text(encoding="utf-8")
            except (UnicodeError, OSError):
                warnings.append(f"verification source unavailable: {verification_source}")
                continue
            if contents == live:
                selected.append(contents)
            else:
                warnings.append(f"verification source changed after selection: {verification_source}")

    if not selected:
        warnings.append(
            f"verification source not selected with current evidence: {verification_source}"
        )

    records: list[dict[str, object]] = []
    found_structured = False
    for snippet in selected:
        parsed = parse_structured_evidence(snippet)
        if not parsed.present:
            continue
        found_structured = True
        if parsed.errors:
            warnings.extend(
                f"invalid structured evidence in {verification_source}: {error}"
                for error in parsed.errors
            )
            continue
        records.extend(parsed.checks)

    if selected and not found_structured:
        warnings.append(f"no structured verification evidence selected from {verification_source}")

    results: list[dict[str, object]] = []
    for target in commands:
        matches = [record for record in records if record.get("command") == target]
        good = [
            record for record in matches
            if record.get("evidence_source") == "command"
            and record.get("status") == "PASS"
            and record.get("exit_code") == 0
        ]
        # Conflicting/failing/inferred records for the same command prevent a
        # PASS even if another record claims to have succeeded.
        valid = (
            bool(good) and len(good) == len(matches)
            and not warnings
        )
        if valid:
            detail = "matching structured PASS command record; execution not independently verified"
        elif not matches:
            detail = "no exact command match in selected structured evidence"
        else:
            detail = "matching records are conflicting, failing, inferred, or invalid"
        results.append({
            "proof": target,
            "status": "represented" if valid else "missing",
            "checks": sorted({str(record["check"]) for record in good}) if valid else [],
            "detail": detail,
        })
    return results, warnings
