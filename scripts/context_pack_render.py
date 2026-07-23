#!/usr/bin/env python3
"""Integrity metadata and Markdown rendering for context packets."""

from __future__ import annotations

import hashlib
import json

from context_pack_model import (
    GENERATED_PACKET_MARKER,
    MAX_OMITTED,
    STRICT_FAIL_EXIT,
    STRICT_WARN_EXIT,
    LoadedRecord,
    RequiredFileResult,
    escape_table_cell,
    format_heading_path,
    safe_fence,
)


def required_summary(required_results: list[RequiredFileResult]) -> str:
    """Render compact required-source metadata."""
    if not required_results:
        return "None"
    return ", ".join(f"{item.file}={item.status}" for item in required_results)


def packet_fingerprint(
    task_text: str,
    budget: int,
    routing_source: str,
    selected_records: list[dict[str, object]],
    required_results: list[RequiredFileResult],
) -> str:
    """Return a stable packet fingerprint without timestamps or absolute paths."""
    payload = {
        "budget": budget,
        "required": [
            {
                "file": item.file,
                "status": item.status,
                "ranges": list(item.represented_ranges),
                "hashes": list(item.content_hashes),
            }
            for item in required_results
        ],
        "routing_source": routing_source,
        "selected": [
            {
                "role": item["role"],
                "file": item["file"],
                "start_line": item["start_line"],
                "end_line": item["end_line"],
                "content_hash": item["content_hash"],
            }
            for item in selected_records
        ],
        "task": task_text,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return f"sha256:{hashlib.sha256(encoded.encode('utf-8')).hexdigest()}"


def determine_status(
    selected_records: list[dict[str, object]],
    required_results: list[RequiredFileResult],
    routing_messages: list[str],
    budget_messages: list[str],
    freshness_messages: list[str],
    stale_index_warnings: list[str],
    fatal_errors: list[str] | None = None,
) -> str:
    """Determine PASS, WARN, or FAIL for the packet."""
    if fatal_errors:
        return "FAIL"
    if not selected_records:
        return "FAIL"
    if any(item.status != "represented" for item in required_results):
        return "FAIL"
    material_freshness = [
        message
        for message in freshness_messages
        if message != "index refreshed before packet generation"
    ]
    if routing_messages or budget_messages or material_freshness or stale_index_warnings:
        return "WARN"
    return "PASS"


def render_packet(
    task_text: str,
    budget: int,
    routing_source: str,
    route_labels: list[str],
    current_records: list[LoadedRecord],
    selected_records: list[dict[str, object]],
    omitted_candidates: list[dict[str, object]],
    routing_messages: list[str],
    budget_messages: list[str],
    freshness_messages: list[str],
    warnings: list[str],
    required_results: list[RequiredFileResult] | None = None,
    fatal_errors: list[str] | None = None,
) -> tuple[str, str]:
    """Render the final Markdown packet and return it with its status."""
    required_results = required_results or []
    fatal_errors = fatal_errors or []
    status = determine_status(
        selected_records,
        required_results,
        routing_messages,
        budget_messages,
        freshness_messages,
        warnings,
        fatal_errors,
    )
    fingerprint = packet_fingerprint(
        task_text, budget, routing_source, selected_records, required_results
    )

    lines = [GENERATED_PACKET_MARKER, "", "# Context Packet", ""]
    lines.extend(
        [
            f"- Packet status: {status}",
            f"- Packet fingerprint: {fingerprint}",
            f"- Task: `{task_text}`",
            (
                "- Effective selected-context budget: approximately "
                f"{budget} tokens (approximate, not a final rendered-output budget)"
            ),
            f"- Selected-context budget: approximately {budget} tokens (approximate, not a final rendered-output budget)",
            f"- Routing source: {routing_source}",
            f"- Route matches: {', '.join(route_labels)}",
            f"- Required sources: {required_summary(required_results)}",
            f"- Markdown records scanned: {len(current_records)}",
            "",
        ]
    )

    if fatal_errors:
        lines.extend(["## Packet errors", ""])
        lines.extend(f"- {error}" for error in fatal_errors)
        lines.append("")

    if routing_messages:
        lines.extend(["## Routing notes", ""])
        lines.extend(f"- {message}" for message in routing_messages)
        lines.append("")
    if budget_messages:
        lines.extend(["## Budget notes", ""])
        lines.extend(f"- {message}" for message in budget_messages)
        lines.append("")
    if freshness_messages:
        lines.extend(["## Index freshness", ""])
        lines.extend(f"- {message}" for message in freshness_messages)
        lines.append("")

    lines.extend(
        [
            "## Hydration contract",
            "",
            "- Required and current-state sources outrank templates and examples.",
            "- Omitted context is unknown, not irrelevant.",
            "- A packet is a narrow task slice, not the complete project state.",
            "- Read the full source when the task expands or a warning directs you to it.",
            "- Treat examples as examples, not current project facts.",
            "",
            "## Required-source results",
            "",
        ]
    )
    if required_results:
        for item in required_results:
            ranges = f"; ranges={','.join(item.represented_ranges)}" if item.represented_ranges else ""
            lines.append(f"- `{item.file}`: {item.status} — {item.detail}{ranges}")
    else:
        lines.append("- None.")
    lines.append("")

    lines.extend(["## Selected context", ""])
    if selected_records:
        lines.extend(
            [
                "| Source role | File | Lines | Heading path | Est. tokens | Content hash | Reason |",
                "| ----------- | ---- | ----- | ------------ | ----------- | ------------ | ------ |",
            ]
        )
        for record in selected_records:
            values = [
                record["role"],
                record["file"],
                f"{record['start_line']}-{record['end_line']}",
                format_heading_path(tuple(record["heading_path"])),
                record["approx_token_estimate"],
                record["content_hash"],
                record["reason"],
            ]
            lines.append("| " + " | ".join(escape_table_cell(value) for value in values) + " |")
    else:
        lines.append("- No records selected.")
        if any("budget" in str(item.get("reason", "")) for item in omitted_candidates):
            lines.append(
                "- No records fit within the packet budget. Increase `--budget` or inspect the omitted candidates directly."
            )
    lines.append("")

    lines.extend(["## Relevant excerpts", ""])
    if selected_records:
        for record in selected_records:
            lines.append(f"### `{record['file']}` {record['start_line']}-{record['end_line']}")
            lines.append("")
            lines.append(f"- Source role: {record['role']}")
            lines.append(f"- Heading path: {format_heading_path(tuple(record['heading_path']))}")
            lines.append(f"- Route: {record['route']}")
            lines.append(f"- Content hash: {record['content_hash']}")
            lines.append("")
            opening, closing = safe_fence(str(record["text"]))
            lines.append(opening)
            lines.append(str(record["text"]).rstrip())
            lines.append(closing)
            lines.append("")
    else:
        lines.extend(["- No excerpts selected.", ""])

    lines.extend(["## Omitted candidates", ""])
    if omitted_candidates:
        for candidate in omitted_candidates[:MAX_OMITTED]:
            lines.append(
                f"- `{candidate['file']}` {candidate['range']} "
                f"({format_heading_path(tuple(candidate['heading_path']))}) - {candidate['reason']}"
            )
    else:
        lines.append("- None.")
    lines.append("")

    lines.extend(["## Stale-index warnings", ""])
    if warnings:
        lines.extend(f"- {warning}" for warning in warnings)
    else:
        lines.append("- None.")
    lines.append("")

    lines.extend(
        [
            "## Refresh guidance",
            "",
            "If Markdown files changed, rebuild the local index and rerun the packet:",
            "",
            "```bash",
            "python scripts/build_context_index.py",
            'python scripts/context_pack.py "<task>"',
            "```",
            "",
            "This packet is a narrow context slice, not a replacement for the repository docs.",
        ]
    )
    return "\n".join(lines), status


def exit_code_for(status: str, strict: bool) -> int:
    """Return the documented CLI exit code for a rendered packet."""
    if not strict:
        return 0
    if status == "WARN":
        return STRICT_WARN_EXIT
    if status == "FAIL":
        return STRICT_FAIL_EXIT
    return 0
