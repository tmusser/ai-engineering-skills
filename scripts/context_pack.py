#!/usr/bin/env python3
"""Generate a small, integrity-aware Markdown context packet for a specific task."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from context_pack_model import (
    DEFAULT_BUDGET,
    DEFAULT_INDEX,
    DEFAULT_ROUTING,
    ROOT,
    STRICT_FAIL_EXIT,
    STRICT_WARN_EXIT,
    clamp_budget,
    load_routes,
    normalize_required_path,
)
from context_pack_data import (
    index_freshness_messages,
    load_records,
    load_saved_index,
    refresh_index,
    select_records,
    stale_warnings,
)
from context_pack_render import exit_code_for, render_packet


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", nargs="*", help="Task string to route into a context packet.")
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
        help="Explicitly rebuild the local Markdown index before generating the packet.",
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
        help="Path to routing rules relative to --root unless absolute.",
    )
    parser.add_argument(
        "--require-file",
        action="append",
        default=[],
        metavar="PATH",
        help="Require a repository-relative Markdown source. Repeat for multiple files.",
    )
    parser.add_argument(
        "--route",
        action="append",
        default=[],
        metavar="ROUTE_NAME",
        help="Explicitly activate a named context route. Repeat for multiple routes.",
    )
    parser.add_argument(
        "--route-only",
        action="store_true",
        help="Use only routes named with --route instead of combining them with automatic routing.",
    )
    parser.add_argument(
        "--list-routes",
        action="store_true",
        help="List available route names and labels, then exit without generating a packet.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help=(
            f"Return {STRICT_WARN_EXIT} for WARN and {STRICT_FAIL_EXIT} for FAIL "
            "after rendering the packet."
        ),
    )
    return parser.parse_args(argv)


def unique_route_names(route_names: list[str]) -> list[str]:
    """Return route names in first-seen order without duplicates."""
    unique: list[str] = []
    for name in route_names:
        if name not in unique:
            unique.append(name)
    return unique


def print_routes(routes: list[object]) -> None:
    """Print configured route names and labels in deterministic order."""
    print("Available context routes:")
    for route in routes:
        print(f"- {route.name}: {route.label}")


def main(argv: list[str] | None = None) -> int:
    """Command-line entry point."""
    args = parse_args(argv)
    root = args.root.expanduser().resolve()

    routes, routing_warnings, routing_source, route_max_budget = load_routes(root, args.routing)
    if args.list_routes:
        print_routes(routes)
        for warning in routing_warnings:
            print(f"warning: {warning}", file=sys.stderr)
        return 0

    task_text = " ".join(args.task).strip()
    if not task_text:
        print("error: task string must not be empty unless --list-routes is used", file=sys.stderr)
        return 2

    explicit_routes = unique_route_names(args.route)
    available_routes = {route.name for route in routes}
    unknown_routes = [name for name in explicit_routes if name not in available_routes]
    if unknown_routes:
        available = ", ".join(route.name for route in routes)
        print(
            f"error: unknown route(s): {', '.join(unknown_routes)}; available routes: {available}",
            file=sys.stderr,
        )
        return 2
    if args.route_only and not explicit_routes:
        print("error: --route-only requires at least one --route ROUTE_NAME", file=sys.stderr)
        return 2

    if args.budget <= 0:
        packet, _ = render_packet(
            task_text=task_text,
            budget=args.budget,
            routing_source="unavailable",
            route_labels=[],
            current_records=[],
            selected_records=[],
            omitted_candidates=[],
            routing_messages=[],
            budget_messages=[],
            freshness_messages=[],
            warnings=[],
            fatal_errors=["--budget must be a positive integer"],
        )
        print(packet)
        return STRICT_FAIL_EXIT

    normalized_required: list[str] = []
    path_errors: list[str] = []
    for raw_path in args.require_file:
        normalized, error = normalize_required_path(raw_path)
        if error:
            path_errors.append(error)
        elif normalized and normalized not in normalized_required:
            normalized_required.append(normalized)

    selected_budget, budget_messages = clamp_budget(args.budget, route_max_budget)

    refresh_note = ""
    if args.refresh_index:
        try:
            refresh_note = refresh_index(root, args.index)
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return 1

    current_records = load_records(root)
    saved_rows, index_warnings = load_saved_index(root, args.index)
    freshness_messages = list(index_warnings)
    freshness_messages.extend(index_freshness_messages(root, args.index))
    if refresh_note:
        freshness_messages.insert(0, refresh_note)
    stale_index_warnings = stale_warnings(current_records, saved_rows)

    selected_records, omitted_candidates, route_labels, _, required_results = select_records(
        task_text=task_text,
        routes=routes,
        records=current_records,
        budget=selected_budget,
        required_files=normalized_required,
        root=root,
        explicit_routes=explicit_routes,
        route_only=args.route_only,
    )

    packet, status = render_packet(
        task_text=task_text,
        budget=selected_budget,
        routing_source=routing_source,
        route_labels=route_labels,
        current_records=current_records,
        selected_records=selected_records,
        omitted_candidates=omitted_candidates,
        routing_messages=list(routing_warnings),
        budget_messages=budget_messages,
        freshness_messages=freshness_messages,
        warnings=stale_index_warnings,
        required_results=required_results,
        fatal_errors=path_errors,
    )
    print(packet)
    if path_errors:
        return STRICT_FAIL_EXIT
    return exit_code_for(status, args.strict)


if __name__ == "__main__":
    raise SystemExit(main())
