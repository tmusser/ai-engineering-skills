#!/usr/bin/env python3
"""Check whether SPEC.md is concrete enough to serve as an auditable contract."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

STATUS_PASS = "PASS"
STATUS_FAIL = "FAIL"
STATUS_REVIEW = "REVIEW_REQUIRED"

HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+(?P<title>.+?)\s*$")
LIST_RE = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)(?P<body>.+?)\s*$")
PRIMARY_FAILURE_RE = re.compile(r"(?i)^\s*primary failure mode(?: for this slice)?\s*:\s*(?P<value>.*)$")
VAGUE_CRITERIA = {
    "works", "works correctly", "it works", "looks good", "done", "all good",
    "no bugs", "functions correctly", "behaves correctly", "works as expected",
}
REQUIRED_SECTIONS = {
    "objective": ("objective",),
    "acceptance criteria": ("acceptance criteria",),
    "non-goals": ("non goals", "non-goals"),
    "spec ceiling": ("spec ceiling",),
    "likely failure modes": ("likely failure modes",),
    "verification demo": ("verification demo",),
    "invalid if": ("invalid if", "invalid-if"),
}


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    details: str


@dataclass(frozen=True)
class Result:
    status: str
    checks: tuple[Check, ...]
    failures: tuple[str, ...]
    review_required: tuple[str, ...]
    spec_path: str
    root: str
    exit_code_policy: str


def normalize_heading(line: str) -> str | None:
    match = HEADING_RE.match(line)
    if not match:
        return None
    title = match.group("title").strip().lower()
    title = re.sub(r"[`*_]", "", title)
    title = re.sub(r"[^a-z0-9\s-]", " ", title)
    return re.sub(r"\s+", " ", title).strip()


def section_lines(text: str, variants: tuple[str, ...]) -> list[str] | None:
    lines = text.splitlines()
    start = None
    start_level = None
    for index, line in enumerate(lines):
        match = HEADING_RE.match(line)
        if not match:
            continue
        heading = normalize_heading(line)
        if heading and heading in variants:
            start = index + 1
            start_level = len(line) - len(line.lstrip("#"))
            break
    if start is None or start_level is None:
        return None

    collected = []
    for line in lines[start:]:
        if HEADING_RE.match(line):
            level = len(line) - len(line.lstrip("#"))
            if level <= start_level:
                break
        collected.append(line)
    return collected


def clean_markdown(value: str) -> str:
    value = value.strip()
    value = re.sub(r"^\s*(?:[-*+]\s+|\d+[.)]\s+|>\s*)", "", value)
    value = value.strip().strip("`")
    value = value.strip("*_")
    return value.strip()


def is_template_guidance(line: str) -> bool:
    stripped = line.strip()
    return len(stripped) >= 2 and stripped.startswith("_") and stripped.endswith("_")


def is_placeholder(value: str) -> bool:
    cleaned = clean_markdown(value).lower()
    return not cleaned or cleaned in {"tbd", "todo", "placeholder"}


def meaningful_lines(lines: list[str] | None) -> list[str]:
    if lines is None:
        return []
    values = []
    for line in lines:
        if not line.strip() or line.strip().startswith("```") or is_template_guidance(line):
            continue
        cleaned = clean_markdown(line)
        if cleaned and not is_placeholder(cleaned):
            values.append(cleaned)
    return values


def list_items(lines: list[str] | None) -> list[str]:
    if lines is None:
        return []
    items = []
    for line in lines:
        match = LIST_RE.match(line)
        if match:
            body = clean_markdown(match.group("body"))
            if body and not is_placeholder(body):
                items.append(body)
    return items


def primary_failure(lines: list[str] | None) -> str | None:
    if lines is None:
        return None
    for index, line in enumerate(lines):
        match = PRIMARY_FAILURE_RE.match(clean_markdown(line))
        if not match:
            continue
        inline = clean_markdown(match.group("value"))
        if inline and not is_placeholder(inline):
            return inline
        for candidate in lines[index + 1:]:
            if HEADING_RE.match(candidate):
                break
            cleaned = clean_markdown(candidate)
            if cleaned and not is_placeholder(cleaned) and not is_template_guidance(candidate):
                return cleaned
        return None
    return None


def parse_reference_rows(lines: list[str] | None) -> list[tuple[str, str, str]]:
    if lines is None:
        return []
    rows = []
    for line in lines:
        stripped = line.strip()
        if not (stripped.startswith("|") and stripped.endswith("|")):
            continue
        cells = [clean_markdown(cell) for cell in stripped.strip("|").split("|")]
        if len(cells) < 3 or cells[0].lower() == "reference":
            continue
        if all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells[:3]):
            continue
        rows.append((cells[0], cells[1], cells[2]))
    return rows


def explicit_none(lines: list[str] | None) -> bool:
    allowed = {"none", "none available", "no authoritative references", "no open questions", "not applicable", "n/a"}
    return any(value.lower().rstrip(".") in allowed for value in meaningful_lines(lines))


def contains_placeholder(lines: list[str] | None) -> bool:
    if lines is None:
        return False
    for line in lines:
        if not line.strip() or is_template_guidance(line):
            continue
        if is_placeholder(clean_markdown(line)):
            return True
    return False


def local_reference_path(reference: str) -> Path | None:
    candidate = clean_markdown(reference)
    if not candidate or candidate.startswith(("http://", "https://", "#")):
        return None
    if any(char in candidate for char in "*?[]") or " " in candidate:
        return None
    candidate = candidate.split("::", 1)[0]
    candidate = re.sub(r"#L\d+(?:-L?\d+)?$", "", candidate)
    candidate = re.sub(r":\d+(?::\d+)?$", "", candidate)
    if not candidate:
        return None
    path = Path(candidate)
    looks_local = candidate.startswith(("./", "../")) or "/" in candidate or path.suffix != ""
    return path if looks_local else None


def evaluate(spec_path: Path, root: Path) -> Result:
    root = root.expanduser().resolve()
    path = spec_path.expanduser()
    if not path.is_absolute():
        path = root / path
    path = path.resolve()
    policy = "PASS=0; FAIL=1; REVIEW_REQUIRED=0 by default, 2 with --strict-review"

    checks = []
    failures = []
    reviews = []

    if not path.is_file():
        message = f"spec not found: {path}"
        return Result(STATUS_FAIL, (Check("spec", STATUS_FAIL, message),), (message,), (), str(path), str(root), policy)

    text = path.read_text(encoding="utf-8")
    sections = {name: section_lines(text, variants) for name, variants in REQUIRED_SECTIONS.items()}

    for name in ("objective", "non-goals", "spec ceiling", "verification demo", "invalid if"):
        lines = sections[name]
        values = meaningful_lines(lines)
        if lines is None:
            detail = f"missing required section: {name}"
            checks.append(Check(name, STATUS_FAIL, detail)); failures.append(detail)
        elif not values:
            detail = f"{name} has no concrete content"
            checks.append(Check(name, STATUS_FAIL, detail)); failures.append(detail)
        else:
            checks.append(Check(name, STATUS_PASS, f"{name} contains concrete content."))

    acceptance = sections["acceptance criteria"]
    acceptance_values = meaningful_lines(acceptance)
    criteria = list_items(acceptance)
    if acceptance is None:
        detail = "missing required section: acceptance criteria"
        checks.append(Check("acceptance criteria", STATUS_FAIL, detail)); failures.append(detail)
    elif not acceptance_values:
        detail = "acceptance criteria has no concrete content"
        checks.append(Check("acceptance criteria", STATUS_FAIL, detail)); failures.append(detail)
    elif not criteria:
        detail = "acceptance criteria is present but not expressed as auditable list items"
        checks.append(Check("acceptance criteria", STATUS_REVIEW, detail)); reviews.append(detail)
    else:
        vague = [criterion for criterion in criteria if re.sub(r"[.!]+$", "", criterion.strip().lower()) in VAGUE_CRITERIA]
        if vague:
            detail = "vague acceptance criterion requires review: " + ", ".join(vague)
            checks.append(Check("acceptance criteria", STATUS_REVIEW, detail)); reviews.append(detail)
        else:
            checks.append(Check("acceptance criteria", STATUS_PASS, f"{len(criteria)} auditable acceptance criterion/criteria detected."))

    failure_lines = sections["likely failure modes"]
    failure_value = primary_failure(failure_lines)
    if failure_lines is None:
        detail = "missing required section: likely failure modes"
        checks.append(Check("primary failure mode", STATUS_FAIL, detail)); failures.append(detail)
    elif failure_value is None:
        detail = "primary failure mode is missing or still a placeholder"
        checks.append(Check("primary failure mode", STATUS_FAIL, detail)); failures.append(detail)
    else:
        checks.append(Check("primary failure mode", STATUS_PASS, f"primary failure mode: {failure_value}"))

    reference_lines = section_lines(text, ("authoritative references",))
    rows = parse_reference_rows(reference_lines)
    if reference_lines is None or explicit_none(reference_lines):
        checks.append(Check("authoritative references", STATUS_PASS, "no authoritative references declared; no reference integrity check required."))
    elif not rows:
        detail = "authoritative references section is present but does not declare a usable reference row or explicit none"
        checks.append(Check("authoritative references", STATUS_REVIEW, detail)); reviews.append(detail)
    else:
        reference_failures = []
        reference_reviews = []
        for reference, governs, delta in rows:
            if is_placeholder(reference) or reference.lower().startswith("file, test, symbol"):
                reference_reviews.append("reference path/artifact is still a placeholder")
                continue
            if is_placeholder(governs) or governs.lower() == "behavior/decision":
                reference_reviews.append(f"{reference}: governed behavior is unresolved")
            if is_placeholder(delta) or delta.lower().startswith("none or explicit"):
                reference_reviews.append(f"{reference}: task-specific delta is unresolved")
            local = local_reference_path(reference)
            if local is not None:
                resolved = local if local.is_absolute() else root / local
                if not resolved.exists():
                    reference_failures.append(f"local authoritative reference not found: {reference}")
        if reference_failures:
            detail = "; ".join(reference_failures)
            checks.append(Check("authoritative references", STATUS_FAIL, detail)); failures.extend(reference_failures)
        elif reference_reviews:
            detail = "; ".join(reference_reviews)
            checks.append(Check("authoritative references", STATUS_REVIEW, detail)); reviews.extend(reference_reviews)
        else:
            checks.append(Check("authoritative references", STATUS_PASS, f"{len(rows)} declared reference row(s) are structurally auditable."))

    open_lines = section_lines(text, ("open questions",))
    if open_lines is not None and contains_placeholder(open_lines):
        detail = "open questions still contain a placeholder; resolve it or state none explicitly"
        checks.append(Check("open questions", STATUS_REVIEW, detail)); reviews.append(detail)
    elif open_lines is not None and meaningful_lines(open_lines) and not explicit_none(open_lines):
        detail = "open questions remain unresolved; confirm they do not change the acceptance boundary"
        checks.append(Check("open questions", STATUS_REVIEW, detail)); reviews.append(detail)
    else:
        checks.append(Check("open questions", STATUS_PASS, "no unresolved open questions detected."))

    status = STATUS_FAIL if failures else STATUS_REVIEW if reviews else STATUS_PASS
    return Result(status, tuple(checks), tuple(failures), tuple(reviews), str(path), str(root), policy)


def emit_text(result: Result) -> None:
    print(f"SPEC GATE: {result.status}")
    print(f"Spec: {result.spec_path}")
    for check in result.checks:
        print(f"- [{check.status}] {check.name}: {check.details}")
    if result.failures:
        print("FAILURES:")
        for item in result.failures:
            print(f"- {item}")
    if result.review_required:
        print("REVIEW REQUIRED:")
        for item in result.review_required:
            print(f"- {item}")


def emit_json(result: Result) -> None:
    print(json.dumps(asdict(result), indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, default=Path("SPEC.md"))
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root used to resolve SPEC.md and local references.")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--strict-review", action="store_true", help="Return exit 2 when the result is REVIEW_REQUIRED.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = evaluate(args.spec, args.root)
    emit_json(result) if args.format == "json" else emit_text(result)
    if result.status == STATUS_FAIL:
        return 1
    if result.status == STATUS_REVIEW and args.strict_review:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
