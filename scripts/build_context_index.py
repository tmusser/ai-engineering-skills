#!/usr/bin/env python3
"""Build a deterministic markdown context index for local packet generation."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = Path(".ai-context/index.jsonl")
EXCLUDED_DIR_NAMES = {
    ".git",
    ".ai-context",
    "__pycache__",
    "build",
    "dist",
    "generated",
    "node_modules",
    "vendor",
}

ATX_HEADING_RE = re.compile(r"^(?P<indent>\s{0,3})(?P<marks>#{1,6})\s+(?P<title>.+?)\s*$")
SETEXT_UNDERLINE_RE = re.compile(r"^\s{0,3}(?P<underline>=+|-+)\s*$")
FENCE_RE = re.compile(r"^\s{0,3}(?P<marker>`{3,}|~{3,})")


@dataclass(frozen=True)
class Heading:
    """One parsed markdown heading."""

    level: int
    title: str
    line_number: int


@dataclass(frozen=True)
class SectionRecord:
    """One indexed markdown section."""

    file: str
    heading_path: tuple[str, ...]
    heading_level: int
    start_line: int
    end_line: int
    approx_token_estimate: int
    content_hash: str
    text: str

    def to_index_row(self) -> dict[str, object]:
        """Return the JSONL payload for the persisted index."""
        return {
            "approx_token_estimate": self.approx_token_estimate,
            "content_hash": self.content_hash,
            "end_line": self.end_line,
            "file": self.file,
            "heading_level": self.heading_level,
            "heading_path": list(self.heading_path),
            "start_line": self.start_line,
        }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help="Repository root to scan (default: repository root containing this script).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Index output path relative to --root unless absolute.",
    )
    return parser.parse_args(argv)


def normalize_heading_text(text: str) -> str:
    """Normalize a heading title for indexing."""
    text = re.sub(r"\s#+\s*$", "", text.strip())
    text = re.sub(r"\s+", " ", text)
    return text


def is_excluded_path(path: Path) -> bool:
    """Return True when a path is inside an excluded directory."""
    return any(part in EXCLUDED_DIR_NAMES for part in path.parts)


def iter_markdown_paths(root: Path) -> list[Path]:
    """Return all markdown files under root in stable order."""
    markdown_paths: list[Path] = []

    for dirpath, dirnames, filenames in os.walk(root):
        current_dir = Path(dirpath)
        try:
            relative_dir = current_dir.relative_to(root)
        except ValueError:
            continue

        if is_excluded_path(relative_dir):
            dirnames[:] = []
            continue

        dirnames[:] = sorted(
            name
            for name in dirnames
            if name not in EXCLUDED_DIR_NAMES and not is_excluded_path(relative_dir / name)
        )

        for filename in sorted(filenames):
            if not filename.lower().endswith(".md"):
                continue

            path = current_dir / filename
            try:
                relative_path = path.relative_to(root)
            except ValueError:
                continue

            if is_excluded_path(relative_path):
                continue

            markdown_paths.append(path)

    return sorted(markdown_paths, key=lambda item: item.relative_to(root).as_posix())


def extract_headings(lines: list[str]) -> list[Heading]:
    """Parse headings from markdown lines, ignoring fenced code blocks."""
    headings: list[Heading] = []
    in_fence = False
    fence_char = ""
    fence_length = 0
    index = 0

    while index < len(lines):
        line = lines[index]
        fence_match = FENCE_RE.match(line)
        if in_fence:
            if fence_match:
                marker = fence_match.group("marker")
                if marker[0] == fence_char and len(marker) >= fence_length:
                    in_fence = False
            index += 1
            continue

        if fence_match:
            marker = fence_match.group("marker")
            in_fence = True
            fence_char = marker[0]
            fence_length = len(marker)
            index += 1
            continue

        atx_match = ATX_HEADING_RE.match(line)
        if atx_match:
            title = normalize_heading_text(atx_match.group("title"))
            if title:
                headings.append(
                    Heading(
                        level=len(atx_match.group("marks")),
                        title=title,
                        line_number=index + 1,
                    )
                )
            index += 1
            continue

        if index + 1 < len(lines):
            underline_match = SETEXT_UNDERLINE_RE.match(lines[index + 1])
            if underline_match and line.strip():
                underline = underline_match.group("underline")
                level = 1 if underline.startswith("=") else 2
                headings.append(
                    Heading(
                        level=level,
                        title=normalize_heading_text(line),
                        line_number=index + 1,
                    )
                )
                index += 2
                continue

        index += 1

    return headings


def section_text(lines: list[str], start_line: int, end_line: int) -> str:
    """Return the markdown section text using 1-based inclusive line numbers."""
    return "\n".join(lines[start_line - 1 : end_line])


def hash_content(text: str) -> str:
    """Return a stable content hash for a section."""
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def estimate_tokens(text: str) -> int:
    """Return a conservative token estimate for a section."""
    return max(1, math.ceil(len(text) / 4))


def build_records_for_file(path: Path, root: Path) -> list[SectionRecord]:
    """Build section records for one markdown file."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    relative_path = path.relative_to(root).as_posix()
    headings = extract_headings(lines)
    records: list[SectionRecord] = []

    if not headings:
        if text.strip():
            normalized_text = "\n".join(lines)
            records.append(
                SectionRecord(
                    file=relative_path,
                    heading_path=(),
                    heading_level=0,
                    start_line=1,
                    end_line=max(1, len(lines)),
                    approx_token_estimate=estimate_tokens(normalized_text),
                    content_hash=hash_content(normalized_text),
                    text=normalized_text,
                )
            )
        return records

    heading_stack: list[Heading] = []

    for heading_index, heading in enumerate(headings):
        while heading_stack and heading_stack[-1].level >= heading.level:
            heading_stack.pop()
        heading_stack.append(heading)

        end_line = len(lines)
        for later_heading in headings[heading_index + 1 :]:
            if later_heading.level <= heading.level:
                end_line = later_heading.line_number - 1
                break

        if end_line < heading.line_number:
            end_line = heading.line_number

        normalized_text = section_text(lines, heading.line_number, end_line)
        records.append(
            SectionRecord(
                file=relative_path,
                heading_path=tuple(item.title for item in heading_stack),
                heading_level=heading.level,
                start_line=heading.line_number,
                end_line=end_line,
                approx_token_estimate=estimate_tokens(normalized_text),
                content_hash=hash_content(normalized_text),
                text=normalized_text,
            )
        )

    return records


def collect_markdown_records(root: Path) -> list[SectionRecord]:
    """Collect all markdown section records under root."""
    records: list[SectionRecord] = []
    for path in iter_markdown_paths(root):
        records.extend(build_records_for_file(path, root))
    return sorted(
        records,
        key=lambda record: (
            record.file,
            record.start_line,
            record.end_line,
            record.heading_level,
            record.heading_path,
        ),
    )


def write_index(root: Path, output: Path) -> int:
    """Write a JSONL index and return the record count."""
    records = collect_markdown_records(root)
    output_path = output if output.is_absolute() else root / output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(
                json.dumps(
                    record.to_index_row(),
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                )
            )
            handle.write("\n")

    return len(records)


def main(argv: list[str] | None = None) -> int:
    """Command-line entry point."""
    args = parse_args(argv)
    root = args.root.expanduser().resolve()
    output = args.output.expanduser()
    count = write_index(root, output)
    output_path = output if output.is_absolute() else root / output
    print(f"wrote {count} markdown records to {output_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
