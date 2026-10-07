#!/usr/bin/env python3
"""Validate whether a fresh session can trust HANDOFF.md enough to resume."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

PASS = 0
STALE = 2
REVIEW_REQUIRED = 3

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_FRESHNESS = Path(__file__).resolve().with_name("handoff_freshness.py")

HEADING_RE = re.compile(r"^\s{0,3}(?P<marks>#{1,6})\s+(?P<title>.+?)\s*$")
FIELD_RE = re.compile(r"^\s*(?:[-*+]\s*)?(?P<label>[^:]+):\s*(?P<value>.*)\s*$")
VERIFY_STATUS_RE = re.compile(
    r"(?im)^\s*Status\s*:\s*(PASS|FAIL|REVIEW_REQUIRED)\s*$"
)
VALID_VERIFY_STATUSES = {"PASS", "FAIL", "REVIEW_REQUIRED", "NOT_PRESENT"}
PLACEHOLDERS = {
    "",
    "-",
    "_tbd_",
    "tbd",
    "n/a",
    "pass | fail | review_required",
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=("check",),
        help="Check whether the handoff can be trusted by a fresh session.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Repository root. Defaults to git rev-parse --show-toplevel.",
    )
    parser.add_argument(
        "--handoff",
        default="HANDOFF.md",
        help="Repository-relative handoff path (default: HANDOFF.md).",
    )
    parser.add_argument(
        "--verify",
        default="VERIFY.md",
        help="Repository-relative verification path (default: VERIFY.md).",
    )
    return parser.parse_args(argv)


def run_git(root: Path | None, args: list[str]) -> str:
    command = ["git"]
    if root is not None:
        command.extend(["-C", str(root)])
    command.extend(args)
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "no output"
        raise ValueError(f"git {' '.join(args)} failed: {detail}")
    return result.stdout.strip()


def resolve_root(explicit_root: Path | None) -> Path:
    if explicit_root is not None:
        root = explicit_root.resolve()
        run_git(root, ["rev-parse", "--show-toplevel"])
        return root
    return Path(run_git(None, ["rev-parse", "--show-toplevel"])).resolve()


def safe_relative(raw: str, label: str) -> str:
    candidate = raw.strip().strip("`").replace("\\", "/")
    pure = PurePosixPath(candidate)
    if not candidate or pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        raise ValueError(f"{label} must be a safe repository-relative path")
    return pure.as_posix()


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().strip("`").strip())


def meaningful(value: str) -> bool:
    normalized = normalize(value)
    return bool(normalized and normalized.lower() not in PLACEHOLDERS and "_tbd_" not in normalized.lower())


def section(text: str, name: str) -> str:
    lines = text.splitlines()
    target = name.strip().lower()
    start: int | None = None
    level = 0
    for index, line in enumerate(lines):
        match = HEADING_RE.match(line)
        if match and match.group("title").strip().lower() == target:
            start = index + 1
            level = len(match.group("marks"))
            break
    if start is None:
        return ""

    collected: list[str] = []
    for line in lines[start:]:
        match = HEADING_RE.match(line)
        if match and len(match.group("marks")) <= level:
            break
        collected.append(line)
    return "\n".join(collected)


def first_field(text: str, *labels: str, allow_none: bool = False) -> str | None:
    wanted = {label.lower() for label in labels}
    for line in text.splitlines():
        match = FIELD_RE.match(line)
        if not match:
            continue
        if match.group("label").strip().lower() not in wanted:
            continue
        value = normalize(match.group("value"))
        if meaningful(value) or (allow_none and value.lower() == "none"):
            return value
    return None


def meaningful_bullets(block: str) -> list[str]:
    values: list[str] = []
    for line in block.splitlines():
        stripped = line.strip()
        if not re.match(r"^[-*+]\s+", stripped):
            continue
        value = re.sub(r"^[-*+]\s+", "", stripped).strip()
        if meaningful(value):
            values.append(normalize(value))
    return values


def parse_required_files(text: str) -> tuple[list[str], list[str]]:
    raw = first_field(text, "Required resume files", allow_none=True)
    if raw is None:
        return [], ["missing Required resume files"]
    if raw.lower() == "none":
        return [], []

    paths: list[str] = []
    errors: list[str] = []
    for token in raw.split(","):
        candidate = token.strip()
        if not candidate:
            continue
        try:
            paths.append(safe_relative(candidate, "required resume file"))
        except ValueError as exc:
            errors.append(str(exc))
    if not paths and not errors:
        errors.append("Required resume files is empty")
    return paths, errors


def recorded_verify_status(text: str | None) -> str:
    if text is None:
        return "NOT_PRESENT"
    block = section(text, "Verify gate") or text
    match = VERIFY_STATUS_RE.search(block)
    return match.group(1) if match else "INCOMPLETE"


def run_freshness(root: Path, handoff: str) -> tuple[str, list[str]]:
    if not DEFAULT_FRESHNESS.is_file():
        return "REVIEW_REQUIRED", [f"handoff freshness guard unavailable: {DEFAULT_FRESHNESS}"]
    result = subprocess.run(
        [
            sys.executable,
            str(DEFAULT_FRESHNESS),
            "check",
            "--root",
            str(root),
            "--handoff",
            handoff,
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    output = "\n".join(part for part in (result.stdout, result.stderr) if part).strip()
    if "HANDOFF FRESHNESS: PASS" in output:
        status = "PASS"
    elif "HANDOFF FRESHNESS: STALE" in output:
        status = "STALE"
    else:
        status = "REVIEW_REQUIRED"
    details = [
        normalize(line.lstrip("- "))
        for line in output.splitlines()[1:]
        if meaningful(line)
    ]
    return status, details


def check_resume_trust(root: Path, handoff_path: str, verify_path: str) -> int:
    handoff_file = root / handoff_path
    if not handoff_file.is_file():
        print(f"HANDOFF RESUME TRUST: REVIEW_REQUIRED\n- missing handoff: {handoff_path}")
        return REVIEW_REQUIRED

    freshness_status, freshness_details = run_freshness(root, handoff_path)
    if freshness_status == "STALE":
        print("HANDOFF RESUME TRUST: STALE")
        for detail in freshness_details:
            print(f"- {detail}")
        print("- action: reconcile live state and regenerate HANDOFF.md before resuming")
        return STALE
    if freshness_status != "PASS":
        print("HANDOFF RESUME TRUST: REVIEW_REQUIRED")
        for detail in freshness_details:
            print(f"- {detail}")
        print("- action: establish handoff freshness before trusting continuation claims")
        return REVIEW_REQUIRED

    handoff_text = handoff_file.read_text(encoding="utf-8")
    verify_file = root / verify_path
    verify_text = verify_file.read_text(encoding="utf-8") if verify_file.is_file() else None
    live_verify = recorded_verify_status(verify_text)

    problems: list[str] = []

    required_files, required_errors = parse_required_files(handoff_text)
    problems.extend(required_errors)
    for relative in required_files:
        if not (root / relative).is_file():
            problems.append(f"required resume file missing: {relative}")

    expected_verify = first_field(handoff_text, "Verify gate status")
    if expected_verify is None:
        problems.append("missing Verify gate status")
    else:
        expected_verify = expected_verify.upper()
        if expected_verify not in VALID_VERIFY_STATUSES:
            problems.append(f"invalid Verify gate status: {expected_verify}")
        elif live_verify == "INCOMPLETE":
            problems.append(f"live verification status is incomplete in {verify_path}")
        elif expected_verify != live_verify:
            problems.append(
                f"verification status mismatch: handoff={expected_verify}, live={live_verify}"
            )

    review_items = first_field(handoff_text, "Review-required items", allow_none=True)
    if review_items is None:
        problems.append("missing Review-required items")
    elif review_items.lower() == "none" and live_verify == "REVIEW_REQUIRED":
        problems.append(
            "handoff says Review-required items: none but live verification is REVIEW_REQUIRED"
        )
    elif review_items.lower() != "none" and live_verify == "PASS":
        problems.append(
            "handoff carries review-required items but live verification status is PASS"
        )

    next_tasks = meaningful_bullets(section(handoff_text, "Next recommended task"))
    if len(next_tasks) != 1:
        problems.append(
            f"expected exactly one next recommended task, found {len(next_tasks)}"
        )

    next_verify = first_field(
        section(handoff_text, "Verification state"),
        "Next verification command",
    )
    if next_verify is None:
        problems.append("missing Next verification command")

    if problems:
        print("HANDOFF RESUME TRUST: REVIEW_REQUIRED")
        print("- freshness: PASS")
        for problem in problems:
            print(f"- {problem}")
        print("- action: reconcile HANDOFF.md with live state before resuming")
        return REVIEW_REQUIRED

    print("HANDOFF RESUME TRUST: PASS")
    print("- freshness: PASS")
    print(f"- required resume files: {len(required_files)} checked")
    print(f"- verification status: {live_verify} matches")
    print("- review-required items: coherent with live verification state")
    print("- next task: exactly one")
    print("- next verification command: present")
    return PASS


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        root = resolve_root(args.root)
        handoff_path = safe_relative(args.handoff, "--handoff")
        verify_path = safe_relative(args.verify, "--verify")
        return check_resume_trust(root, handoff_path, verify_path)
    except (OSError, ValueError) as exc:
        print(f"HANDOFF RESUME TRUST: REVIEW_REQUIRED\n- {exc}", file=sys.stderr)
        return REVIEW_REQUIRED


if __name__ == "__main__":
    raise SystemExit(main())
