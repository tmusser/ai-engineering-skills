#!/usr/bin/env python3
"""Generate a small Markdown context packet for a specific task."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INDEX = Path(".ai-context/index.jsonl")
DEFAULT_ROUTING = Path(".ai-context/routing.yml")
DEFAULT_BUDGET = 700
MAX_SELECTED_CONTEXT_BUDGET = 1500
MAX_EXCERPT_LINES = 12
MAX_OMITTED = 6


@dataclass(frozen=True)
class RouteSpec:
    """One routing rule for packet generation."""

    name: str
    label: str
    keywords: tuple[str, ...]
    files: tuple[str, ...]


@dataclass(frozen=True)
class LoadedRecord:
    """One fresh markdown section with text."""

    file: str
    heading_path: tuple[str, ...]
    heading_level: int
    start_line: int
    end_line: int
    approx_token_estimate: int
    content_hash: str
    text: str

    def key(self) -> tuple[str, tuple[str, ...], int, int, int]:
        """Return a stable identity for stale-index checks."""
        return (
            self.file,
            self.heading_path,
            self.heading_level,
            self.start_line,
            self.end_line,
        )


def load_index_builder():
    """Load the index builder module without requiring package installation."""
    module_path = ROOT / "scripts" / "build_context_index.py"
    spec = importlib.util.spec_from_file_location("build_context_index", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BUILD_INDEX = load_index_builder()


DEFAULT_ROUTES: tuple[RouteSpec, ...] = (
    RouteSpec(
        name="resume_handoff",
        label="Resume / handoff",
        keywords=("handoff", "resume", "fresh context", "resume packet", "continuation"),
        files=(
            "templates/HANDOFF.md",
            "skills/handoff/SKILL.md",
            "docs/recipes.md",
        ),
    ),
    RouteSpec(
        name="verification",
        label="Verification",
        keywords=("verify", "verification", "evidence", "review required", "review_required"),
        files=(
            "templates/VERIFY.md",
            "skills/verify-contract/SKILL.md",
            "skills/test-mini/SKILL.md",
            "docs/recipes.md",
        ),
    ),
    RouteSpec(
        name="scope_control",
        label="Scope control",
        keywords=("scope", "boundary", "freeze", "blast radius", "unrelated edits"),
        files=(
            "skills/scope-freeze/SKILL.md",
            "docs/recipes.md",
            "docs/skill-map.md",
        ),
    ),
    RouteSpec(
        name="planning",
        label="Planning",
        keywords=("plan", "spec", "checklist", "mini-spec", "thin-plan"),
        files=(
            "skills/mini-spec/SKILL.md",
            "skills/thin-plan/SKILL.md",
            "templates/SPEC.md",
            "templates/PLAN.md",
        ),
    ),
    RouteSpec(
        name="debugging",
        label="Debugging",
        keywords=("debug", "bug", "diagnose", "failure", "regression", "loop"),
        files=(
            "skills/diagnose-loop/SKILL.md",
            "skills/bug-capture/SKILL.md",
            "docs/recipes.md",
        ),
    ),
    RouteSpec(
        name="shipping",
        label="Shipping",
        keywords=("ship", "release", "deploy", "publish", "rollout"),
        files=(
            "skills/ship-mini/SKILL.md",
            "docs/release-checklist.md",
            "docs/agent-worker-safety.md",
        ),
    ),
)

OVERVIEW_FALLBACK: tuple[RouteSpec, ...] = (
    RouteSpec(
        name="overview",
        label="Overview",
        keywords=("context", "overview", "docs", "readme", "start"),
        files=(
            "README.md",
            "docs/skill-map.md",
            "docs/recipes.md",
        ),
    ),
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", nargs="+", help="Task string to route into a context packet.")
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help="Repository root to scan (default: repository root containing this script).",
    )
    parser.add_argument(
        "--budget",
        type=int,
        default=DEFAULT_BUDGET,
        help="Approximate selected-context budget for the packet (default: 700).",
    )
    parser.add_argument(
        "--refresh-index",
        action="store_true",
        help="Explicitly rebuild the local markdown index before generating the packet.",
    )
    parser.add_argument(
        "--index",
        type=Path,
        default=DEFAULT_INDEX,
        help="Path to the saved context index relative to --root unless absolute.",
    )
    parser.add_argument(
        "--routing",
        type=Path,
        default=DEFAULT_ROUTING,
        help="Path to the routing rules file relative to --root unless absolute.",
    )
    return parser.parse_args(argv)


def normalize_text(text: str) -> str:
    """Normalize text for keyword matching."""
    return re.sub(r"\s+", " ", text.lower()).strip()


def tokenize(text: str) -> list[str]:
    """Return lower-case word tokens."""
    return re.findall(r"[a-z0-9_]+", text.lower())


def resolve_repo_path(root: Path, path: Path) -> Path:
    """Resolve a repo-relative path against the selected root."""
    return path if path.is_absolute() else root / path


def load_routes(root: Path, routing_path: Path) -> tuple[list[RouteSpec], list[str], str, int]:
    """Load routing rules with a built-in fallback."""
    path = resolve_repo_path(root, routing_path)
    warnings: list[str] = []

    if not path.exists():
        warnings.append(f"routing file missing: {path}")
        return list(DEFAULT_ROUTES), warnings, "built-in", MAX_SELECTED_CONTEXT_BUDGET

    try:
        routes, configured_max_budget = parse_route_file(path.read_text(encoding="utf-8"))
    except OSError as exc:
        warnings.append(f"unable to read routing file: {exc}")
        return list(DEFAULT_ROUTES), warnings, "built-in", MAX_SELECTED_CONTEXT_BUDGET
    except ValueError as exc:
        warnings.append(f"routing file parse failed: {exc}")
        return list(DEFAULT_ROUTES), warnings, "built-in", MAX_SELECTED_CONTEXT_BUDGET

    if not routes:
        warnings.append("routing file did not define any routes")
        return list(DEFAULT_ROUTES), warnings, "built-in", MAX_SELECTED_CONTEXT_BUDGET

    max_selected_context_tokens = configured_max_budget or MAX_SELECTED_CONTEXT_BUDGET
    if max_selected_context_tokens > MAX_SELECTED_CONTEXT_BUDGET:
        warnings.append(
            "routing max_selected_context_tokens "
            f"{max_selected_context_tokens} exceeds hard max {MAX_SELECTED_CONTEXT_BUDGET}; "
            f"clamped to {MAX_SELECTED_CONTEXT_BUDGET}"
        )
        max_selected_context_tokens = MAX_SELECTED_CONTEXT_BUDGET

    return routes, warnings, "file", max_selected_context_tokens


def parse_route_file(text: str) -> tuple[list[RouteSpec], int | None]:
    """Parse the tiny routing.yml format used by this repo."""
    routes: list[RouteSpec] = []
    configured_max_budget: int | None = None
    current_name: str | None = None
    current_label = ""
    current_keywords: list[str] = []
    current_files: list[str] = []
    seen_routes_header = False

    def flush() -> None:
        nonlocal current_name, current_label, current_keywords, current_files
        if current_name is None:
            return
        routes.append(
            RouteSpec(
                name=current_name,
                label=current_label or current_name.replace("_", " ").title(),
                keywords=tuple(item for item in current_keywords if item),
                files=tuple(item for item in current_files if item),
            )
        )
        current_name = None
        current_label = ""
        current_keywords = []
        current_files = []

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            continue

        if not seen_routes_header:
            if stripped == "routes:":
                seen_routes_header = True
                continue

            if line.startswith(" "):
                raise ValueError(f"unexpected routing line before routes header: {line}")

            if ":" not in stripped:
                raise ValueError(f"unexpected routing line: {line}")

            key, value = stripped.split(":", 1)
            value = value.strip()

            if key == "max_selected_context_tokens":
                configured_max_budget = parse_positive_int(value)
                continue

            raise ValueError(f"unsupported top-level key: {key}")

        if line.startswith("  ") and line.endswith(":") and line.count(":") == 1:
            flush()
            current_name = stripped[:-1]
            current_label = ""
            current_keywords = []
            current_files = []
            continue

        if current_name is None or not line.startswith("    "):
            raise ValueError(f"unexpected routing line: {line}")

        key, value = stripped.split(":", 1)
        value = value.strip()

        if key == "label":
            current_label = value
        elif key == "keywords":
            current_keywords = split_csv(value)
        elif key == "files":
            current_files = split_csv(value)
        else:
            raise ValueError(f"unsupported routing key: {key}")

    flush()

    if not seen_routes_header:
        raise ValueError("missing top-level routes: header")

    return routes, configured_max_budget


def split_csv(value: str) -> list[str]:
    """Split a comma-separated scalar into trimmed values."""
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_positive_int(value: str) -> int:
    """Parse a positive integer from a routing scalar."""
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"invalid integer value: {value}") from exc

    if parsed <= 0:
        raise ValueError("max_selected_context_tokens must be a positive integer")

    return parsed


def load_records(root: Path) -> list[LoadedRecord]:
    """Collect the fresh markdown records for packet generation."""
    fresh_records = []
    for record in BUILD_INDEX.collect_markdown_records(root):
        fresh_records.append(
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
        )
    return fresh_records


def load_saved_index(root: Path, index_path: Path) -> tuple[dict[tuple[str, tuple[str, ...], int, int, int], dict[str, object]], list[str]]:
    """Load the persisted index and return keyed rows plus warnings."""
    path = resolve_repo_path(root, index_path)
    warnings: list[str] = []

    if not path.exists():
        warnings.append(
            f"index missing: {path}; rerun with --refresh-index or run python scripts/build_context_index.py"
        )
        return {}, warnings

    rows: dict[tuple[str, tuple[str, ...], int, int, int], dict[str, object]] = {}
    try:
        with path.open(encoding="utf-8") as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                stripped = raw_line.strip()
                if not stripped:
                    continue
                row = json.loads(stripped)
                heading_path = tuple(row.get("heading_path", []))
                key = (
                    str(row["file"]),
                    heading_path,
                    int(row["heading_level"]),
                    int(row["start_line"]),
                    int(row["end_line"]),
                )
                rows[key] = row
    except OSError as exc:
        warnings.append(f"unable to read index: {exc}")
        return {}, warnings
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        warnings.append(f"index parse failed: {exc}")
        return {}, warnings

    return rows, warnings


def refresh_index(root: Path, index_path: Path) -> str:
    """Rebuild the saved markdown index and return a packet note."""
    output_path = resolve_repo_path(root, index_path)
    try:
        BUILD_INDEX.write_index(root, output_path)
    except OSError as exc:
        raise RuntimeError(f"unable to refresh index at {output_path}: {exc}") from exc
    except Exception as exc:  # pragma: no cover - defensive guard for refresh failures.
        raise RuntimeError(f"unable to refresh index at {output_path}: {exc}") from exc

    return "index refreshed before packet generation"


def index_freshness_messages(root: Path, index_path: Path) -> list[str]:
    """Return warnings when the saved index is older than current markdown files."""
    path = resolve_repo_path(root, index_path)
    if not path.exists():
        return []

    try:
        index_mtime_ns = path.stat().st_mtime_ns
    except OSError as exc:
        return [f"unable to stat index: {exc}"]

    newest_markdown_mtime_ns = index_mtime_ns
    index_is_older = False
    warnings: list[str] = []

    for markdown_path in BUILD_INDEX.iter_markdown_paths(root):
        try:
            markdown_mtime_ns = markdown_path.stat().st_mtime_ns
        except OSError as exc:
            warnings.append(f"unable to stat markdown file: {markdown_path}: {exc}")
            continue

        if markdown_mtime_ns > newest_markdown_mtime_ns:
            newest_markdown_mtime_ns = markdown_mtime_ns
            index_is_older = True

    if index_is_older:
        warnings.append(
            "index older than markdown files; rerun with --refresh-index or run python scripts/build_context_index.py"
        )

    return warnings


def clamp_budget(requested_budget: int, max_budget: int) -> tuple[int, list[str]]:
    """Clamp a requested packet budget and return any visible notes."""
    if requested_budget <= max_budget:
        return requested_budget, []

    return max_budget, [
        f"requested budget {requested_budget} exceeds max {max_budget}; clamped to {max_budget}"
    ]


def select_routes(task_text: str, routes: list[RouteSpec]) -> list[tuple[RouteSpec, int]]:
    """Rank routes against the task string."""
    normalized_task = normalize_text(task_text)
    task_tokens = set(tokenize(task_text))
    ranked: list[tuple[RouteSpec, int]] = []

    for route in routes:
        score = 0
        for keyword in route.keywords:
            normalized_keyword = normalize_text(keyword)
            if normalized_keyword and normalized_keyword in normalized_task:
                score += 1
        route_tokens = set(tokenize(route.name.replace("_", " ")) + tokenize(route.label))
        score += len(task_tokens & route_tokens)
        if score > 0:
            ranked.append((route, score))

    ranked.sort(key=lambda item: (-item[1], routes.index(item[0])))
    return ranked


def record_search_text(record: LoadedRecord) -> str:
    """Return searchable text for a record."""
    heading_text = " ".join(record.heading_path)
    return normalize_text(" ".join([record.file, heading_text, record.text]))


def rank_records_for_route(
    route: RouteSpec,
    records: list[LoadedRecord],
    task_text: str,
) -> list[tuple[int, LoadedRecord, str]]:
    """Score records for one route."""
    task_tokens = set(tokenize(task_text))
    candidates: list[tuple[int, LoadedRecord, str]] = []

    for record in records:
        searchable = record_search_text(record)
        score = 0
        reasons: list[str] = []

        if route.files and record.file in route.files:
            score += 12
            reasons.append("preferred file")

        keyword_hits = 0
        for keyword in route.keywords:
            normalized_keyword = normalize_text(keyword)
            if normalized_keyword and normalized_keyword in searchable:
                keyword_hits += 1
        if keyword_hits:
            score += keyword_hits * 4
            reasons.append(f"{keyword_hits} route keyword hit(s)")

        record_tokens = set(
            tokenize(record.file)
            + tokenize(" ".join(record.heading_path))
            + tokenize(record.text)
        )
        task_hits = len(task_tokens & record_tokens)
        if task_hits:
            score += task_hits
            reasons.append(f"{task_hits} task token hit(s)")

        if score > 0:
            candidates.append((score, record, ", ".join(reasons) if reasons else "matched route"))

    candidates.sort(
        key=lambda item: (
            -item[0],
            item[1].file,
            item[1].start_line,
            item[1].end_line,
            item[1].heading_path,
        )
    )
    return candidates


def select_records(
    task_text: str,
    routes: list[RouteSpec],
    records: list[LoadedRecord],
    budget: int,
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[str], list[str]]:
    """Select records for the packet and report omitted candidates."""
    selected_records: list[dict[str, object]] = []
    omitted_candidates: list[dict[str, object]] = []
    selected_keys: set[tuple[str, tuple[str, ...], int, int, int]] = set()
    omitted_keys: set[tuple[str, tuple[str, ...], int, int, int]] = set()
    used_tokens = 0

    ranked_routes = select_routes(task_text, routes)
    if not ranked_routes:
        ranked_routes = [(route, 0) for route in OVERVIEW_FALLBACK]

    route_candidates = [
        (route, route_score, rank_records_for_route(route, records, task_text))
        for route, route_score in ranked_routes
    ]
    matched_route_labels = [route.label for route, _, _ in route_candidates]
    route_names = [route.name for route, _, _ in route_candidates]

    if any(candidates for _, _, candidates in route_candidates) and not any(
        record.approx_token_estimate <= budget
        for _, _, candidates in route_candidates
        for _, record, _ in candidates
    ):
        low_budget_candidates: list[dict[str, object]] = []
        for route, route_score, candidates in route_candidates:
            for record_score, record, reason in candidates:
                record_key = record.key()
                if record_key in selected_keys or record_key in omitted_keys:
                    continue
                low_budget_candidates.append(
                    {
                        "file": record.file,
                        "heading_path": record.heading_path,
                        "range": f"{record.start_line}-{record.end_line}",
                        "reason": f"exceeds budget: {route.label}: {reason}",
                    }
                )
                omitted_keys.add(record_key)
                if len(low_budget_candidates) >= MAX_OMITTED:
                    break
            if len(low_budget_candidates) >= MAX_OMITTED:
                break
        return selected_records, low_budget_candidates, matched_route_labels, route_names

    for route, route_score, candidates in route_candidates:
        for record_score, record, reason in candidates[:2]:
            record_key = record.key()
            candidate = {
                "approx_token_estimate": record.approx_token_estimate,
                "end_line": record.end_line,
                "file": record.file,
                "heading_level": record.heading_level,
                "heading_path": record.heading_path,
                "reason": f"{route.label}: {reason}",
                "route": route.label,
                "route_score": route_score,
                "start_line": record.start_line,
                "text": record.text,
            }

            if record_key in selected_keys:
                continue

            if used_tokens + record.approx_token_estimate <= budget:
                selected_records.append(candidate)
                selected_keys.add(record_key)
                used_tokens += record.approx_token_estimate
            else:
                if record_key not in omitted_keys:
                    omitted_candidates.append(
                        {
                            "file": record.file,
                            "heading_path": record.heading_path,
                            "range": f"{record.start_line}-{record.end_line}",
                            "reason": "budget",
                        }
                    )
                    omitted_keys.add(record_key)

    remaining_candidates: list[dict[str, object]] = []
    for route, route_score, candidates in route_candidates:
        for record_score, record, reason in candidates:
            record_key = record.key()
            if record_key in selected_keys:
                continue
            if record_key in omitted_keys:
                continue
            remaining_candidates.append(
                {
                    "file": record.file,
                    "heading_path": record.heading_path,
                    "range": f"{record.start_line}-{record.end_line}",
                    "reason": "lower score" if route_score > 0 else "fallback candidate",
                }
            )
            omitted_keys.add(record_key)

    return selected_records, remaining_candidates, matched_route_labels, route_names


def load_current_and_saved_index(
    root: Path, index_path: Path
) -> tuple[list[LoadedRecord], dict[tuple[str, tuple[str, ...], int, int, int], dict[str, object]], list[str]]:
    """Load current records and saved index data with warnings."""
    current_records = load_records(root)
    saved_rows, warnings = load_saved_index(root, index_path)
    return current_records, saved_rows, warnings


def stale_warnings(
    current_records: list[LoadedRecord],
    saved_rows: dict[tuple[str, tuple[str, ...], int, int, int], dict[str, object]],
) -> list[str]:
    """Return stale index warnings comparing current records and saved rows."""
    warnings: list[str] = []
    if not saved_rows:
        return warnings

    current_rows = {record.key(): record for record in current_records}

    for key, row in sorted(saved_rows.items(), key=lambda item: (item[0][0], item[0][3], item[0][4], item[0][1])):
        current_record = current_rows.get(key)
        if current_record is None:
            warnings.append(
                f"index entry no longer matches current markdown: {row['file']} {row.get('heading_path', [])} {row.get('start_line')}-{row.get('end_line')}"
            )
            continue
        if current_record.content_hash != row.get("content_hash"):
            warnings.append(
                f"stale content hash: {row['file']} {row.get('heading_path', [])} {row.get('start_line')}-{row.get('end_line')}"
            )

    for key, record in sorted(current_rows.items(), key=lambda item: (item[0][0], item[0][3], item[0][4], item[0][1])):
        if key not in saved_rows:
            warnings.append(
                f"missing index entry for current markdown: {record.file} {list(record.heading_path)} {record.start_line}-{record.end_line}"
            )

    return warnings


def format_heading_path(heading_path: tuple[str, ...]) -> str:
    """Format a heading path for markdown output."""
    if not heading_path:
        return "(file root)"
    return " > ".join(heading_path)


def format_excerpt(text: str) -> str:
    """Format a compact excerpt for a markdown packet."""
    lines = text.splitlines()
    if len(lines) > MAX_EXCERPT_LINES:
        lines = lines[:MAX_EXCERPT_LINES] + ["..."]
    return "\n".join(lines).rstrip()


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
) -> str:
    """Render the final markdown packet."""
    lines: list[str] = []
    lines.append("# Context Packet")
    lines.append("")
    lines.append(f"- Task: `{task_text}`")
    lines.append(
        f"- Selected-context budget: approximately {budget} tokens (approximate, not a final rendered-output budget)"
    )
    lines.append(f"- Routing source: {routing_source}")
    lines.append(f"- Route matches: {', '.join(route_labels)}")
    lines.append(f"- Markdown records scanned: {len(current_records)}")
    lines.append("")

    if routing_messages:
        lines.append("## Routing notes")
        lines.append("")
        for message in routing_messages:
            lines.append(f"- {message}")
        lines.append("")

    if budget_messages:
        lines.append("## Budget notes")
        lines.append("")
        for message in budget_messages:
            lines.append(f"- {message}")
        lines.append("")

    if freshness_messages:
        lines.append("## Index freshness")
        lines.append("")
        for message in freshness_messages:
            lines.append(f"- {message}")
        lines.append("")

    lines.append("## Selected context")
    lines.append("")
    if selected_records:
        lines.append("| File | Lines | Heading path | Est. tokens | Reason |")
        lines.append("| ---- | ----- | ------------ | ----------- | ------ |")
        for record in selected_records:
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{record['file']}`",
                        f"`{record['start_line']}-{record['end_line']}`",
                        format_heading_path(record["heading_path"]),
                        str(record["approx_token_estimate"]),
                        str(record["reason"]),
                    ]
                )
                + " |"
            )
    else:
        lines.append("- No records selected.")
        if any(
            "exceeds budget" in str(candidate.get("reason", ""))
            for candidate in omitted_candidates
        ):
            lines.append(
                "- No records fit within the packet budget. Increase `--budget` or inspect the omitted candidates directly."
            )
    lines.append("")

    lines.append("## Relevant excerpts")
    lines.append("")
    if selected_records:
        for record in selected_records:
            lines.append(
                f"### `{record['file']}` {record['start_line']}-{record['end_line']}"
            )
            lines.append("")
            lines.append(f"- Heading path: {format_heading_path(record['heading_path'])}")
            lines.append(f"- Route: {record['route']}")
            lines.append("")
            lines.append("```md")
            lines.append(format_excerpt(str(record["text"])))
            lines.append("```")
            lines.append("")
    else:
        lines.append("- No excerpts selected.")
        lines.append("")

    lines.append("## Omitted candidates")
    lines.append("")
    if omitted_candidates:
        for candidate in omitted_candidates[:MAX_OMITTED]:
            lines.append(
                f"- `{candidate['file']}` {candidate['range']} ({format_heading_path(candidate['heading_path'])}) - {candidate['reason']}"
            )
    else:
        lines.append("- None.")
    lines.append("")

    lines.append("## Stale-index warnings")
    lines.append("")
    if warnings:
        for warning in warnings:
            lines.append(f"- {warning}")
    else:
        lines.append("- None.")
    lines.append("")

    lines.append("## Refresh guidance")
    lines.append("")
    lines.append("If Markdown files changed, rebuild the local index and rerun the packet:")
    lines.append("")
    lines.append("```bash")
    lines.append("python scripts/build_context_index.py")
    lines.append("python scripts/context_pack.py \"<task>\"")
    lines.append("```")
    lines.append("")
    lines.append("This packet is a narrow context slice, not a replacement for the repo docs.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """Command-line entry point."""
    args = parse_args(argv)
    root = args.root.expanduser().resolve()
    task_text = " ".join(args.task).strip()
    if not task_text:
        raise SystemExit("task string must not be empty")

    routes, routing_warnings, routing_source, route_max_budget = load_routes(root, args.routing)
    routing_messages = list(routing_warnings)
    selected_budget, clamp_messages = clamp_budget(args.budget, route_max_budget)
    budget_messages = clamp_messages

    if args.refresh_index:
        try:
            refresh_note = refresh_index(root, args.index)
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return 1
    else:
        refresh_note = ""

    current_records, saved_rows, index_warnings = load_current_and_saved_index(root, args.index)
    freshness_messages = list(index_warnings)
    freshness_messages.extend(index_freshness_messages(root, args.index))
    if refresh_note:
        freshness_messages.insert(0, refresh_note)

    stale_index_warnings = stale_warnings(current_records, saved_rows)

    selected_records, omitted_candidates, route_labels, _ = select_records(
        task_text=task_text,
        routes=routes,
        records=current_records,
        budget=selected_budget,
    )

    packet = render_packet(
        task_text=task_text,
        budget=selected_budget,
        routing_source=routing_source,
        route_labels=route_labels,
        current_records=current_records,
        selected_records=selected_records,
        omitted_candidates=omitted_candidates,
        routing_messages=routing_messages,
        budget_messages=budget_messages,
        freshness_messages=freshness_messages,
        warnings=stale_index_warnings,
    )
    sys.stdout.write(packet)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
