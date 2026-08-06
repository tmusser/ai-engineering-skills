#!/usr/bin/env python3
"""Enforce a persisted scope-freeze contract against the live Git diff."""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable


STATUS_PASS = "PASS"
STATUS_FAIL = "FAIL"
STATUS_REVIEW = "REVIEW_REQUIRED"

PLACEHOLDERS = {"", "-", "_tbd_", "tbd", "n/a", "yes/no"}
FIELD_RE = re.compile(
    r"^\s*(?:[-*+]\s*)?(?P<label>[A-Za-z][A-Za-z0-9 /_-]*?):\s*(?P<value>.*)\s*$"
)
LIST_RE = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)(?P<value>.+?)\s*$")
MAX_FILES_RE = re.compile(r"^\s*(?:[-*+]\s*)?Max files changed:\s*(?P<value>\d+)\s*$", re.I)
RENAMES_RE = re.compile(r"^\s*(?:[-*+]\s*)?Renames allowed:\s*(?P<value>yes|no)\s*$", re.I)
DELETIONS_RE = re.compile(r"^\s*(?:[-*+]\s*)?Deletions allowed:\s*(?P<value>yes|no)\s*$", re.I)

DEFAULT_TRIGGER_PATTERNS = {
    "tests changed": (
        "tests/**",
        "**/test_*.py",
        "**/*_test.py",
        "**/*.spec.*",
        "**/*.test.*",
    ),
    "fixture/data changed": (
        "fixtures/**",
        "**/fixtures/**",
        "data/**",
        "**/data/**",
        "*.csv",
        "*.jsonl",
        "*.parquet",
    ),
    "fixtures changed": (
        "fixtures/**",
        "**/fixtures/**",
        "data/**",
        "**/data/**",
    ),
    "dependencies changed": (
        "requirements*.txt",
        "pyproject.toml",
        "poetry.lock",
        "package.json",
        "package-lock.json",
        "pnpm-lock.yaml",
        "yarn.lock",
        "Cargo.toml",
        "Cargo.lock",
        "go.mod",
        "go.sum",
    ),
    "workflow files changed": (".github/workflows/**",),
    "schemas changed": (
        "schemas/**",
        "**/schemas/**",
        "**/*.schema.*",
    ),
    "migrations changed": (
        "migrations/**",
        "**/migrations/**",
    ),
}


@dataclass(frozen=True)
class ChangedFile:
    """One changed path from git diff or the untracked-file set."""

    status: str
    path: str
    old_path: str | None = None


@dataclass(frozen=True)
class ScopeContract:
    """Machine-enforceable subset of a scope-freeze artifact."""

    task: str
    allowed_writes: tuple[str, ...]
    read_only: tuple[str, ...]
    forbidden: tuple[str, ...]
    review_triggers: tuple[str, ...]
    stop_when: str
    invalid_if: str
    max_files_changed: int | None
    renames_allowed: bool | None
    deletions_allowed: bool | None
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class Result:
    """Scope gate result for text and JSON output."""

    status: str
    failures: tuple[str, ...]
    review_required: tuple[str, ...]
    warnings: tuple[str, ...]
    changed_files: tuple[ChangedFile, ...]
    contract: ScopeContract | None
    exit_code_policy: str


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().strip("`").strip())


def meaningful(value: str) -> bool:
    candidate = normalize(value).lower()
    return bool(candidate and candidate not in PLACEHOLDERS and "_tbd_" not in candidate)


def normalize_path_pattern(value: str) -> str:
    value = normalize(value)
    if value.startswith("./"):
        value = value[2:]
    return value.replace("\\", "/")


def split_inline_values(value: str) -> list[str]:
    value = value.strip()
    if not value:
        return []
    if value.lower() in {"none", "no", "not applicable"}:
        return []
    if "," in value:
        return [part.strip() for part in value.split(",") if part.strip()]
    return [value]


def field_values(text: str, label: str) -> tuple[bool, list[str]]:
    """Return whether a field exists and its inline or following list values."""

    lines = text.splitlines()
    wanted = label.lower()
    for index, line in enumerate(lines):
        match = FIELD_RE.match(line)
        if not match or match.group("label").strip().lower() != wanted:
            continue

        values = split_inline_values(match.group("value"))
        cursor = index + 1
        while cursor < len(lines):
            next_line = lines[cursor]
            if FIELD_RE.match(next_line):
                break
            list_match = LIST_RE.match(next_line)
            if list_match:
                values.extend(split_inline_values(list_match.group("value")))
            elif next_line.strip() and not next_line.startswith((" ", "\t")):
                break
            cursor += 1
        return True, values
    return False, []


def first_field(text: str, label: str) -> str | None:
    present, values = field_values(text, label)
    if not present:
        return None
    if not values:
        return ""
    return normalize(values[0])


def validate_pattern(pattern: str) -> str | None:
    if not pattern:
        return "empty path pattern"
    pure = PurePosixPath(pattern)
    if pure.is_absolute() or pattern.startswith("/"):
        return f"absolute path pattern is not allowed: {pattern}"
    if ".." in pure.parts:
        return f"parent traversal is not allowed: {pattern}"
    return None


def path_matches(path: str, patterns: Iterable[str]) -> bool:
    path = normalize_path_pattern(path)
    path_obj = PurePosixPath(path)
    for raw_pattern in patterns:
        pattern = normalize_path_pattern(raw_pattern)
        if not pattern:
            continue
        if pattern in {"*", "**", "**/*"}:
            return True
        if pattern.endswith("/"):
            if path.startswith(pattern):
                return True
            continue
        if not any(token in pattern for token in "*?[]"):
            if path == pattern or path.startswith(pattern.rstrip("/") + "/"):
                return True
        try:
            if path_obj.match(pattern):
                return True
        except ValueError:
            pass
        if fnmatch.fnmatchcase(path, pattern):
            return True
    return False


def looks_like_path_pattern(value: str) -> bool:
    value = normalize_path_pattern(value)
    if value.lower() in DEFAULT_TRIGGER_PATTERNS:
        return False
    return (
        "/" in value
        or value.startswith(".")
        or any(token in value for token in "*?[]")
        or bool(re.search(r"\.[A-Za-z0-9_-]+$", value))
    )


def parse_scope(text: str) -> tuple[ScopeContract | None, tuple[str, ...]]:
    errors: list[str] = []
    warnings: list[str] = []

    if "SCOPE FREEZE" not in text.upper():
        errors.append("missing SCOPE FREEZE marker")

    task = first_field(text, "Task")
    stop_when = first_field(text, "Stop when")
    invalid_if = first_field(text, "Invalid if")
    allowed_present, allowed = field_values(text, "Allowed writes")
    read_only_present, read_only = field_values(text, "Read-only")
    forbidden_present, forbidden = field_values(text, "Forbidden")
    _, review_triggers = field_values(text, "Review required if")

    if task is None or not meaningful(task):
        errors.append("missing meaningful Task")
    if not allowed_present:
        errors.append("missing Allowed writes")
    if not read_only_present:
        warnings.append("Read-only field not present")
    if not forbidden_present:
        errors.append("missing Forbidden")
    if stop_when is None or not meaningful(stop_when):
        errors.append("missing meaningful Stop when")
    if invalid_if is None or not meaningful(invalid_if):
        errors.append("missing meaningful Invalid if")

    normalized_allowed = tuple(normalize_path_pattern(item) for item in allowed if meaningful(item))
    normalized_read_only = tuple(normalize_path_pattern(item) for item in read_only if meaningful(item))
    normalized_forbidden = tuple(
        normalize_path_pattern(item)
        for item in forbidden
        if meaningful(item) and looks_like_path_pattern(item)
    )
    ignored_forbidden = [
        normalize(item)
        for item in forbidden
        if meaningful(item) and not looks_like_path_pattern(item)
    ]
    if ignored_forbidden:
        warnings.append(
            "non-path forbidden operations are advisory only: " + ", ".join(ignored_forbidden)
        )

    for pattern in (*normalized_allowed, *normalized_read_only, *normalized_forbidden):
        issue = validate_pattern(pattern)
        if issue:
            errors.append(issue)

    max_files_changed: int | None = None
    renames_allowed: bool | None = None
    deletions_allowed: bool | None = None
    for line in text.splitlines():
        if match := MAX_FILES_RE.match(line):
            max_files_changed = int(match.group("value"))
        elif match := RENAMES_RE.match(line):
            renames_allowed = match.group("value").lower() == "yes"
        elif match := DELETIONS_RE.match(line):
            deletions_allowed = match.group("value").lower() == "yes"

    if errors:
        return None, tuple(errors)

    assert task is not None
    assert stop_when is not None
    assert invalid_if is not None
    return (
        ScopeContract(
            task=task,
            allowed_writes=normalized_allowed,
            read_only=normalized_read_only,
            forbidden=normalized_forbidden,
            review_triggers=tuple(normalize(item) for item in review_triggers if meaningful(item)),
            stop_when=stop_when,
            invalid_if=invalid_if,
            max_files_changed=max_files_changed,
            renames_allowed=renames_allowed,
            deletions_allowed=deletions_allowed,
            warnings=tuple(warnings),
        ),
        (),
    )


def git_changed_files(root: Path, base: str) -> tuple[tuple[ChangedFile, ...], str | None]:
    try:
        diff = subprocess.run(
            [
                "git",
                "diff",
                "--name-status",
                "--diff-filter=ACMRTUXBD",
                base,
            ],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
        untracked = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = exc.stderr.strip() if isinstance(exc, subprocess.CalledProcessError) else str(exc)
        return (), "unable to inspect git state" + (f": {detail}" if detail else "")

    changes: list[ChangedFile] = []
    seen: set[tuple[str, str, str | None]] = set()
    for line in diff.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0].strip()
        if status.startswith(("R", "C")) and len(parts) >= 3:
            change = ChangedFile(status=status, old_path=parts[1].strip(), path=parts[2].strip())
        else:
            change = ChangedFile(status=status, path=parts[-1].strip())
        key = (change.status, change.path, change.old_path)
        if key not in seen:
            seen.add(key)
            changes.append(change)

    for line in untracked.stdout.splitlines():
        path = line.strip()
        if not path:
            continue
        key = ("A", path, None)
        if key not in seen:
            seen.add(key)
            changes.append(ChangedFile(status="A", path=path))

    return tuple(changes), None


def change_paths(change: ChangedFile) -> tuple[str, ...]:
    return (change.path,) if change.old_path is None else (change.old_path, change.path)


def trigger_patterns(trigger: str) -> tuple[str, ...]:
    normalized = normalize(trigger).lower()
    if normalized in DEFAULT_TRIGGER_PATTERNS:
        return DEFAULT_TRIGGER_PATTERNS[normalized]
    if looks_like_path_pattern(trigger):
        return (normalize_path_pattern(trigger),)
    return ()


def evaluate(root: Path, base: str, scope_path: Path) -> Result:
    target = root / scope_path
    if not target.is_file():
        return Result(
            status=STATUS_REVIEW,
            failures=(),
            review_required=(f"scope artifact not found: {scope_path}",),
            warnings=(),
            changed_files=(),
            contract=None,
            exit_code_policy="PASS=0, FAIL=1, REVIEW_REQUIRED=0 (or 2 with --strict-review)",
        )

    contract, parse_errors = parse_scope(target.read_text(encoding="utf-8"))
    if contract is None:
        return Result(
            status=STATUS_REVIEW,
            failures=(),
            review_required=tuple(f"invalid scope contract: {item}" for item in parse_errors),
            warnings=(),
            changed_files=(),
            contract=None,
            exit_code_policy="PASS=0, FAIL=1, REVIEW_REQUIRED=0 (or 2 with --strict-review)",
        )

    changed_files, diff_error = git_changed_files(root, base)
    if diff_error:
        return Result(
            status=STATUS_REVIEW,
            failures=(),
            review_required=(diff_error,),
            warnings=contract.warnings,
            changed_files=(),
            contract=contract,
            exit_code_policy="PASS=0, FAIL=1, REVIEW_REQUIRED=0 (or 2 with --strict-review)",
        )

    scope_relative = normalize_path_pattern(scope_path.as_posix())
    governed_changes = tuple(
        change
        for change in changed_files
        if scope_relative not in change_paths(change)
    )
    warnings = list(contract.warnings)
    if len(governed_changes) != len(changed_files):
        warnings.append(
            f"scope artifact excluded from its own write boundary: {scope_relative}"
        )
    unobservable_triggers = [
        trigger for trigger in contract.review_triggers if not trigger_patterns(trigger)
    ]
    if unobservable_triggers:
        warnings.append(
            "non-path review triggers require human judgment: "
            + ", ".join(unobservable_triggers)
        )

    failures: list[str] = []
    reviews: list[str] = []

    if (
        contract.max_files_changed is not None
        and len(governed_changes) > contract.max_files_changed
    ):
        failures.append(
            "changed-file budget exceeded: "
            f"{len(governed_changes)} > {contract.max_files_changed}"
        )

    for change in governed_changes:
        paths = change_paths(change)
        touched_forbidden = [path for path in paths if path_matches(path, contract.forbidden)]
        touched_read_only = [path for path in paths if path_matches(path, contract.read_only)]
        outside_allowed = [path for path in paths if not path_matches(path, contract.allowed_writes)]

        if touched_forbidden:
            failures.append(
                f"forbidden write ({change.status}): " + ", ".join(touched_forbidden)
            )
        if touched_read_only:
            failures.append(
                f"read-only path modified ({change.status}): " + ", ".join(touched_read_only)
            )
        if outside_allowed:
            failures.append(
                f"out-of-scope write ({change.status}): " + ", ".join(outside_allowed)
            )
        if change.status.startswith("R") and contract.renames_allowed is False:
            failures.append(
                f"rename not allowed: {change.old_path} -> {change.path}"
            )
        if change.status.startswith("D") and contract.deletions_allowed is False:
            failures.append(f"deletion not allowed: {change.path}")

    for trigger in contract.review_triggers:
        patterns = trigger_patterns(trigger)
        if not patterns:
            continue
        touched = sorted(
            {
                path
                for change in governed_changes
                for path in change_paths(change)
                if path_matches(path, patterns)
            }
        )
        if touched:
            reviews.append(f"{trigger}: " + ", ".join(touched))

    status = STATUS_FAIL if failures else STATUS_REVIEW if reviews else STATUS_PASS
    return Result(
        status=status,
        failures=tuple(dict.fromkeys(failures)),
        review_required=tuple(dict.fromkeys(reviews)),
        warnings=tuple(warnings),
        changed_files=governed_changes,
        contract=contract,
        exit_code_policy="PASS=0, FAIL=1, REVIEW_REQUIRED=0 (or 2 with --strict-review)",
    )


def emit_text(result: Result) -> None:
    print(f"SCOPE GATE: {result.status}")
    if result.contract is not None:
        print(f"- task: {result.contract.task}")
        allowed = ", ".join(result.contract.allowed_writes) or "none"
        print(f"- allowed writes: {allowed}")
    if result.changed_files:
        print("- changed files:")
        for change in result.changed_files:
            if change.old_path:
                print(f"  - {change.status}: {change.old_path} -> {change.path}")
            else:
                print(f"  - {change.status}: {change.path}")
    for failure in result.failures:
        print(f"- FAIL: {failure}")
    for review in result.review_required:
        print(f"- REVIEW_REQUIRED: {review}")
    for warning in result.warnings:
        print(f"- NOTE: {warning}")


def emit_json(result: Result) -> None:
    payload = {
        "status": result.status,
        "failures": list(result.failures),
        "review_required": list(result.review_required),
        "warnings": list(result.warnings),
        "changed_files": [asdict(change) for change in result.changed_files],
        "contract": asdict(result.contract) if result.contract is not None else None,
        "exit_code_policy": result.exit_code_policy,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, help="Git base commit or ref.")
    parser.add_argument(
        "--scope",
        type=Path,
        default=Path("SCOPE.md"),
        help="Scope artifact path (default: SCOPE.md).",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("."),
        help="Repository root (default: current directory).",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument(
        "--strict-review",
        action="store_true",
        help="Return exit code 2 for REVIEW_REQUIRED.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = evaluate(args.root.resolve(), args.base, args.scope)
    if args.format == "json":
        emit_json(result)
    else:
        emit_text(result)
    if result.status == STATUS_FAIL:
        return 1
    if result.status == STATUS_REVIEW and args.strict_review:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
