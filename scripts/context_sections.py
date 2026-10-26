#!/usr/bin/env python3
"""Optional complete-section coverage for selected eco-mode context.

This verifies explicit source inclusion, not semantic adequacy or executed proof.
"""

from __future__ import annotations

import re
from pathlib import Path

from context_sufficiency import PACKET_MARKER, safe_source, verified_excerpts

ATX_HEADING = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+|$)(.*)$")
OPEN_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(?:.*)$")


def parse_requirement(value: str) -> tuple[str, str]:
    """Decode FILE::Heading; don't silently choose among ambiguous forms."""
    if value.count("::") != 1:
        raise ValueError(f"--require-heading expects FILE::Heading: {value!r}")
    name, heading = value.split("::", 1)
    if not name or not heading.strip() or heading != heading.strip():
        raise ValueError(f"--require-heading expects FILE::Heading: {value!r}")
    return name, heading


def headings_in_source(lines: list[str]) -> list[tuple[int, int, str]]:
    """Find 1-based ATX headings outside Markdown fenced-code blocks."""
    found: list[tuple[int, int, str]] = []
    fence: tuple[str, int] | None = None
    for index, line in enumerate(lines, 1):
        marker = OPEN_FENCE.match(line)
        if fence is not None:
            if marker is not None:
                run = marker.group(1)
                if run[0] == fence[0] and len(run) >= fence[1] and not line[marker.end(1):].strip():
                    fence = None
            continue
        if marker:
            run = marker.group(1)
            fence = (run[0], len(run))
            continue
        match = ATX_HEADING.match(line)
        if match:
            title = re.sub(r"[ \t]+#+[ \t]*$", "", match.group(2)).strip()
            if title:
                found.append((index, len(match.group(1)), title))
    return found


def required_section(source_text: str, heading: str) -> tuple[str | None, str]:
    """Return the unique heading and full subtree until the next peer heading."""
    lines = source_text.splitlines()
    headings = headings_in_source(lines)
    normalized = " ".join(heading.split()).casefold()
    matches = [
        index for index, (_, _, title) in enumerate(headings)
        if " ".join(title.split()).casefold() == normalized
    ]
    if not matches:
        return None, "heading absent from current source"
    if len(matches) > 1:
        return None, "heading occurs more than once; name a unique heading"
    position = matches[0]
    start, level, _ = headings[position]
    end = len(lines)
    for following_line, following_level, _ in headings[position + 1:]:
        if following_level <= level:
            end = following_line - 1
            break
    return "\n".join(lines[start - 1:end]).rstrip(), f"source lines {start}-{end}"


def check_headings(
    payloads: list[tuple[str, str]],
    root: Path,
    requirements: list[str],
) -> list[dict[str, str]]:
    """Require a complete section in a direct file or a verified packet excerpt."""
    direct: dict[Path, str] = {}
    excerpts: dict[str, list[str]] = {}
    for label, text in payloads:
        if text.startswith(PACKET_MARKER):
            verified, _warnings = verified_excerpts(text, root)
            for name, slices in verified.items():
                excerpts.setdefault(name, []).extend(slices)
        elif label != "<stdin>":
            direct[Path(label).resolve()] = text
    results: list[dict[str, str]] = []
    for raw in requirements:
        name, heading = parse_requirement(raw)
        path = safe_source(root, name)
        try:
            current = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise ValueError(f"cannot read heading source {name}: {exc}") from exc
        section, detail = required_section(current, heading)
        if section is None:
            status = "missing"
        else:
            whole_file_selected = direct.get(path) == current
            excerpt_selected = any(section in excerpt for excerpt in excerpts.get(name, []))
            status = "represented" if whole_file_selected or excerpt_selected else "missing"
            if status == "missing":
                detail += "; complete section not in selected context"
        results.append({
            "requirement": raw,
            "source": name,
            "heading": heading,
            "status": status,
            "detail": detail,
        })
    return results
