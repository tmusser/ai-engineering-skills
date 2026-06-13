"""Tiny discount CLI after the fix."""

from __future__ import annotations

import argparse


ROWS = [
    ("SKU-100", "10%"),
    ("SKU-200", "15%"),
    ("SKU-300", "20%"),
    ("SKU-400", "25%"),
]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="discount_cli",
        description="Print discount rows.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit the number of discount rows printed.",
    )
    return parser.parse_args(argv)


def render_rows(limit: int | None = None) -> str:
    visible_rows = ROWS if limit is None else ROWS[:limit]
    lines = ["sku | discount"]
    lines.extend(f"{sku} | {discount}" for sku, discount in visible_rows)
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    print(render_rows(args.limit))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
