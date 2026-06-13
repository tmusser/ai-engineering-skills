"""Tiny discount CLI before the fix."""

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
    return parser.parse_args(argv)


def render_rows() -> str:
    lines = ["sku | discount"]
    lines.extend(f"{sku} | {discount}" for sku, discount in ROWS)
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parse_args(argv)
    print(render_rows())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
