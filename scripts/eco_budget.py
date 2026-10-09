#!/usr/bin/env python3
"""Check selected UTF-8 context files against a local byte budget, not API tokens."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DEFAULT_MAX_BYTES = 60_000


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="UTF-8 files; use '-' once for stdin")
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser.parse_args(argv)


def measure(paths: list[str]) -> tuple[list[dict[str, object]], int]:
    entries: list[dict[str, object]] = []
    total = 0
    seen_stdin = False
    for name in paths:
        if name == "-":
            if seen_stdin:
                raise ValueError("stdin ('-') may be used only once")
            seen_stdin = True
            data = sys.stdin.buffer.read()
            label = "<stdin>"
        else:
            path = Path(name)
            if not path.is_file():
                raise ValueError(f"not a regular file: {name}")
            try:
                data = path.read_bytes()
            except OSError as exc:
                raise ValueError(f"cannot read {name}: {exc}") from exc
            label = name
        try:
            data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"not UTF-8: {label}") from exc
        size = len(data)
        total += size
        entries.append({"path": label, "bytes": size})
    return entries, total


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.max_bytes <= 0:
        print("error: --max-bytes must be positive", file=sys.stderr)
        return 2
    try:
        entries, total = measure(args.paths)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    status = "PASS" if total <= args.max_bytes else "REVIEW_REQUIRED"
    result = {
        "status": status,
        "selected_bytes": total,
        "max_bytes": args.max_bytes,
        "remaining_bytes": args.max_bytes - total,
        "inputs": entries,
        "scope": "selected UTF-8 payload only, not model tokens or full request",
    }
    if args.format == "json":
        print(json.dumps(result, sort_keys=True))
    else:
        print(f"ECO {status}: {total}/{args.max_bytes} selected UTF-8 bytes")
        for entry in entries:
            print(f"- {entry['path']}: {entry['bytes']} bytes")
        print("System/tool/history context and provider token/cost usage unmeasured.")
    return 0 if status == "PASS" else 3


if __name__ == "__main__":
    raise SystemExit(main())
