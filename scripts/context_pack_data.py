#!/usr/bin/env python3
"""Index loading and deterministic context selection."""

from __future__ import annotations

import json
from pathlib import Path

from context_pack_model import (
    BUILD_INDEX,
    OVERVIEW_FALLBACK,
    PER_ROUTE_SELECTION_LIMIT,
    SOURCE_ROLE_PRIORITY,
    LoadedRecord,
    RequiredFileResult,
    RouteSpec,
    normalized_content,
    normalize_text,
    record_search_text,
    resolve_repo_path,
    select_routes,
    source_role,
    tokenize,
)


def load_records(root: Path) -> list[LoadedRecord]:
    """Collect current Markdown records for packet generation."""
    return [
        LoadedRecord(
            file=record.file,
            heading_path=tuple(record.heading_path),
            heading_level=record.heading_level,
            start_line=record.start_line,
            end_line=record.end_line,
            approx_token_estimate=record.approx_token_estimate,
            content_hash=record.content_hash,
            text=record.text,
        )
        for record in BUILD_INDEX.collect_markdown_records(root)
    ]


def load_saved_index(
    root: Path, index_path: Path
) -> tuple[dict[tuple[str, tuple[str, ...], int, int, int], dict[str, object]], list[str]]:
    """Load persisted index rows plus any warnings."""
    path = resolve_repo_path(root, index_path)
    if not path.exists():
        return {}, [
            f"index missing: {path}; rerun with --refresh-index or run python scripts/build_context_index.py"
        ]

    rows: dict[tuple[str, tuple[str, ...], int, int, int], dict[str, object]] = {}
    try:
        with path.open(encoding="utf-8") as handle:
            for raw_line in handle:
                stripped = raw_line.strip()
                if not stripped:
                    continue
                row = json.loads(stripped)
                key = (
                    str(row["file"]),
                    tuple(row.get("heading_path", [])),
                    int(row["heading_level"]),
                    int(row["start_line"]),
                    int(row["end_line"]),
                )
                rows[key] = row
    except OSError as exc:
        return {}, [f"unable to read index: {exc}"]
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return {}, [f"index parse failed: {exc}"]
    return rows, []


def refresh_index(root: Path, index_path: Path) -> str:
    """Rebuild the saved Markdown index and return a packet note."""
    output_path = resolve_repo_path(root, index_path)
    try:
        BUILD_INDEX.write_index(root, output_path)
    except OSError as exc:
        raise RuntimeError(f"unable to refresh index at {output_path}: {exc}") from exc
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(f"unable to refresh index at {output_path}: {exc}") from exc
    return "index refreshed before packet generation"


def index_freshness_messages(root: Path, index_path: Path) -> list[str]:
    """Warn when the saved index is older than current Markdown sources."""
    path = resolve_repo_path(root, index_path)
    if not path.exists():
        return []
    try:
        index_mtime_ns = path.stat().st_mtime_ns
    except OSError as exc:
        return [f"unable to stat index: {exc}"]

    warnings: list[str] = []
    for markdown_path in BUILD_INDEX.iter_markdown_paths(root):
        try:
            if markdown_path.stat().st_mtime_ns > index_mtime_ns:
                warnings.append(
                    "index older than markdown files; rerun with --refresh-index or run "
                    "python scripts/build_context_index.py"
                )
                break
        except OSError as exc:
            warnings.append(f"unable to stat markdown file: {markdown_path}: {exc}")
    return warnings


def stale_warnings(
    current_records: list[LoadedRecord],
    saved_rows: dict[tuple[str, tuple[str, ...], int, int, int], dict[str, object]],
) -> list[str]:
    """Compare current records with saved index rows."""
    if not saved_rows:
        return []
    warnings: list[str] = []
    current_rows = {record.key(): record for record in current_records}
    for key, row in sorted(saved_rows.items(), key=lambda item: item[0]):
        current_record = current_rows.get(key)
        if current_record is None:
            warnings.append(
                f"index entry no longer matches current markdown: {row['file']} "
                f"{row.get('heading_path', [])} {row.get('start_line')}-{row.get('end_line')}"
            )
        elif current_record.content_hash != row.get("content_hash"):
            warnings.append(
                f"stale content hash: {row['file']} {row.get('heading_path', [])} "
                f"{row.get('start_line')}-{row.get('end_line')}"
            )
    for key, record in sorted(current_rows.items(), key=lambda item: item[0]):
        if key not in saved_rows:
            warnings.append(
                f"missing index entry for current markdown: {record.file} "
                f"{list(record.heading_path)} {record.start_line}-{record.end_line}"
            )
    return warnings


def rank_records_for_route(
    route: RouteSpec,
    records: list[LoadedRecord],
    task_text: str,
    required_files: set[str],
    require_task_hit: bool = False,
) -> list[tuple[int, LoadedRecord, str, str]]:
    """Score all relevant records for one route."""
    task_tokens = set(tokenize(task_text))
    candidates: list[tuple[int, LoadedRecord, str, str]] = []
    for record in records:
        searchable = record_search_text(record)
        score = 0
        reasons: list[str] = []
        if record.file in route.files:
            score += 12
            reasons.append("preferred file")
        keyword_hits = sum(
            1
            for keyword in route.keywords
            if normalize_text(keyword) and normalize_text(keyword) in searchable
        )
        if keyword_hits:
            score += keyword_hits * 4
            reasons.append(f"{keyword_hits} route keyword hit(s)")
        record_tokens = set(
            tokenize(record.file) + tokenize(" ".join(record.heading_path)) + tokenize(record.text)
        )
        task_hits = len(task_tokens & record_tokens)
        if task_hits:
            score += task_hits
            reasons.append(f"{task_hits} task token hit(s)")
        if score <= 0 or (require_task_hit and task_hits <= 0):
            continue
        role = source_role(record.file, required_files)
        candidates.append((score, record, ", ".join(reasons) or "matched route", role))

    candidates.sort(
        key=lambda item: (
            -SOURCE_ROLE_PRIORITY[item[3]],
            -item[0],
            item[1].approx_token_estimate,
            item[1].file,
            item[1].start_line,
            item[1].end_line,
            item[1].heading_path,
        )
    )
    return candidates


def ranges_overlap(left: dict[str, object], right: LoadedRecord) -> bool:
    """Return True if two selections overlap in the same file."""
    if left["file"] != right.file:
        return False
    return not (int(left["end_line"]) < right.start_line or right.end_line < int(left["start_line"]))


def selection_rank(role: str, score: int, record: LoadedRecord) -> tuple[int, int, int]:
    """Return a deterministic rank used for redundant candidate resolution."""
    return (SOURCE_ROLE_PRIORITY[role], score, -record.approx_token_estimate)


def make_candidate(
    record: LoadedRecord,
    role: str,
    route_label: str,
    reason: str,
    route_score: int,
    record_score: int,
    required: bool = False,
) -> dict[str, object]:
    """Create one selected-context candidate payload."""
    return {
        "approx_token_estimate": record.approx_token_estimate,
        "content_hash": record.content_hash,
        "end_line": record.end_line,
        "file": record.file,
        "heading_level": record.heading_level,
        "heading_path": record.heading_path,
        "reason": reason,
        "record_score": record_score,
        "required": required,
        "role": role,
        "route": route_label,
        "route_score": route_score,
        "start_line": record.start_line,
        "text": record.text,
        "selection_rank": selection_rank(role, record_score, record),
    }


def append_omitted(
    omitted: list[dict[str, object]],
    record: LoadedRecord,
    reason: str,
) -> None:
    """Append one unique omitted candidate."""
    key = (record.file, record.start_line, record.end_line, reason)
    if any(
        (item["file"], item["start_line"], item["end_line"], item["reason"]) == key
        for item in omitted
    ):
        return
    omitted.append(
        {
            "file": record.file,
            "heading_path": record.heading_path,
            "start_line": record.start_line,
            "end_line": record.end_line,
            "range": f"{record.start_line}-{record.end_line}",
            "reason": reason,
        }
    )


def add_candidate(
    selected: list[dict[str, object]],
    candidate: dict[str, object],
    budget: int,
    used_tokens: int,
) -> tuple[bool, int, str]:
    """Add or replace a candidate while enforcing budget and redundancy guards."""
    record = LoadedRecord(
        file=str(candidate["file"]),
        heading_path=tuple(candidate["heading_path"]),
        heading_level=int(candidate["heading_level"]),
        start_line=int(candidate["start_line"]),
        end_line=int(candidate["end_line"]),
        approx_token_estimate=int(candidate["approx_token_estimate"]),
        content_hash=str(candidate["content_hash"]),
        text=str(candidate["text"]),
    )
    normalized = normalized_content(record.text)
    redundant_indexes = [
        index
        for index, existing in enumerate(selected)
        if ranges_overlap(existing, record) or normalized_content(str(existing["text"])) == normalized
    ]

    if redundant_indexes:
        best_existing = max(
            (selected[index] for index in redundant_indexes),
            key=lambda item: tuple(item["selection_rank"]),
        )
        if bool(best_existing["required"]):
            return False, used_tokens, "redundant with required selection"
        if tuple(candidate["selection_rank"]) <= tuple(best_existing["selection_rank"]):
            return False, used_tokens, "redundant lower-ranked candidate"

        removed_tokens = sum(int(selected[index]["approx_token_estimate"]) for index in redundant_indexes)
        replacement_tokens = used_tokens - removed_tokens + record.approx_token_estimate
        if replacement_tokens > budget:
            return False, used_tokens, "replacement exceeds budget"
        selected[:] = [item for index, item in enumerate(selected) if index not in redundant_indexes]
        selected.append(candidate)
        return True, replacement_tokens, "replaced lower-ranked redundant selection"

    if used_tokens + record.approx_token_estimate > budget:
        return False, used_tokens, "budget"
    selected.append(candidate)
    return True, used_tokens + record.approx_token_estimate, "selected"


def required_file_candidates(
    required_file: str,
    records: list[LoadedRecord],
    task_text: str,
) -> list[LoadedRecord]:
    """Rank sections inside one required file."""
    task_tokens = set(tokenize(task_text))
    candidates = [record for record in records if record.file == required_file]
    return sorted(
        candidates,
        key=lambda record: (
            -len(
                task_tokens
                & set(
                    tokenize(record.file)
                    + tokenize(" ".join(record.heading_path))
                    + tokenize(record.text)
                )
            ),
            record.approx_token_estimate,
            -record.heading_level,
            record.start_line,
            record.end_line,
        ),
    )


def select_records(
    task_text: str,
    routes: list[RouteSpec],
    records: list[LoadedRecord],
    budget: int,
    required_files: list[str] | None = None,
    root: Path | None = None,
) -> tuple[
    list[dict[str, object]],
    list[dict[str, object]],
    list[str],
    list[str],
    list[RequiredFileResult],
]:
    """Select authoritative, non-redundant records and report omissions."""
    required_files = required_files or []
    required_set = set(required_files)
    selected: list[dict[str, object]] = []
    omitted: list[dict[str, object]] = []
    required_results: list[RequiredFileResult] = []
    used_tokens = 0

    for required_file in required_files:
        path = (root / required_file) if root is not None else None
        if path is not None and (not path.is_file() or path.is_symlink()):
            required_results.append(
                RequiredFileResult(required_file, "missing", "required source is missing or not a regular file")
            )
            continue

        candidates = required_file_candidates(required_file, records, task_text)
        if not candidates:
            required_results.append(
                RequiredFileResult(required_file, "missing", "required source was not indexed")
            )
            continue

        represented: list[str] = []
        hashes: list[str] = []
        for record in candidates:
            candidate = make_candidate(
                record=record,
                role="required",
                route_label="Required source",
                reason="required file",
                route_score=10_000,
                record_score=10_000,
                required=True,
            )
            added, used_tokens, add_reason = add_candidate(selected, candidate, budget, used_tokens)
            if added:
                represented.append(f"{record.start_line}-{record.end_line}")
                hashes.append(record.content_hash)
                break
            append_omitted(omitted, record, f"required source: {add_reason}")

        if represented:
            required_results.append(
                RequiredFileResult(
                    required_file,
                    "represented",
                    "required source selected",
                    tuple(represented),
                    tuple(hashes),
                )
            )
        else:
            required_results.append(
                RequiredFileResult(
                    required_file,
                    "cannot_fit",
                    "no non-redundant section from the required source fit the effective budget",
                )
            )

    ranked_routes = select_routes(task_text, routes)
    if not ranked_routes:
        ranked_routes = [(route, 0) for route in OVERVIEW_FALLBACK]
    route_labels = [route.label for route, _ in ranked_routes]
    route_names = [route.name for route, _ in ranked_routes]

    for route, route_score in ranked_routes:
        selected_for_route = 0
        candidates = rank_records_for_route(
            route, records, task_text, required_set, require_task_hit=(route_score == 0)
        )
        for record_score, record, reason, role in candidates:
            if selected_for_route >= PER_ROUTE_SELECTION_LIMIT:
                append_omitted(omitted, record, "per-route selection limit")
                continue
            candidate = make_candidate(
                record=record,
                role=role,
                route_label=route.label,
                reason=f"{route.label}: {reason}",
                route_score=route_score,
                record_score=record_score,
            )
            added, used_tokens, add_reason = add_candidate(selected, candidate, budget, used_tokens)
            if added:
                selected_for_route += 1
            else:
                append_omitted(
                    omitted, record, "exceeds budget" if add_reason == "budget" else add_reason
                )

    selected.sort(
        key=lambda item: (
            -SOURCE_ROLE_PRIORITY[str(item["role"])],
            -int(item["record_score"]),
            str(item["file"]),
            int(item["start_line"]),
        )
    )
    return selected, omitted, route_labels, route_names, required_results
