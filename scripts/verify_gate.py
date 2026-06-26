#!/usr/bin/env python3
"""Deterministic verify-gate checker for AI Engineering Skills."""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


STATUS_PASS = "PASS"
STATUS_FAIL = "FAIL"
STATUS_REVIEW = "REVIEW_REQUIRED"

DEFAULT_TEST_PATTERNS = [
    "tests/**",
    "**/test_*.py",
    "**/*_test.py",
    "**/*.spec.*",
    "**/*.test.*",
]

DEFAULT_FIXTURE_PATTERNS = [
    "fixtures/**",
    "data/**",
    "examples/**/data/**",
    "*.csv",
    "*.jsonl",
    "*.parquet",
]

DEFAULT_DEPENDENCY_PATTERNS = [
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
]

HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+(?P<title>.+?)\s*$")
VERIFY_STATUS_RE = re.compile(r"(?im)^\s*status\s*:\s*(PASS|FAIL|REVIEW_REQUIRED)\s*$")
INLINE_PATH_DECL_RE = re.compile(
    r"^\s*(?:[-*+]\s*)?(?P<label>protected|forbidden)\s+paths?(?:\s+\w+)*\s*:\s*(?P<value>.+?)\s*$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ChangedFile:
    """One changed file as reported by git."""

    status: str
    path: str
    old_path: str | None = None


@dataclass(frozen=True)
class Check:
    """One check result for text and JSON output."""

    name: str
    status: str
    details: str


@dataclass(frozen=True)
class Result:
    """Computed verify-gate outcome."""

    status: str
    checks: list[Check]
    failures: list[str]
    review_required: list[str]
    changed_files: list[str]
    changed_file_statuses: list[ChangedFile]
    exit_code_policy: str


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, help="Git base commit to diff against.")
    parser.add_argument("--spec", default="SPEC.md", help="Path to SPEC.md (default: SPEC.md).")
    parser.add_argument(
        "--verify",
        default="VERIFY.md",
        help="Path to VERIFY.md (default: VERIFY.md).",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format.",
    )
    parser.add_argument(
        "--strict-review",
        action="store_true",
        help="Treat REVIEW_REQUIRED as a nonzero exit.",
    )
    return parser.parse_args(argv)


def normalize_heading(line: str) -> str | None:
    """Normalize a markdown heading for tolerant matching."""
    match = HEADING_RE.match(line)
    if not match:
        return None

    title = match.group("title").strip().lower()
    title = re.sub(r"[`*_]", "", title)
    title = re.sub(r"[^a-z0-9\s\-]", " ", title)
    title = re.sub(r"\s+", " ", title).strip()
    return title


def concept_present(text: str, variants: list[str]) -> bool:
    """Return True when any variant appears in a heading or prose."""
    lowered = text.lower()
    if any(variant in lowered for variant in variants):
        return True

    for line in text.splitlines():
        heading = normalize_heading(line)
        if heading and any(variant in heading for variant in variants):
            return True

    return False


def section_lines(text: str, heading_variants: list[str]) -> list[str]:
    """Return the lines in the first matching section."""
    lines = text.splitlines()
    start_index: int | None = None

    for index, line in enumerate(lines):
        heading = normalize_heading(line)
        if heading and any(variant in heading for variant in heading_variants):
            start_index = index + 1
            break

    if start_index is None:
        return []

    collected: list[str] = []
    for line in lines[start_index:]:
        if normalize_heading(line):
            break
        collected.append(line)

    return collected


def extract_declared_paths(text: str, label: str) -> list[str]:
    """Collect explicit path declarations from a markdown document."""
    declared: list[str] = []
    seen: set[str] = set()
    label_lower = label.lower()

    def add_candidate(candidate: str) -> None:
        candidate = candidate.strip().strip("`").strip()
        if not candidate or candidate.lower() in {"_tbd_", "tbd", "none", "yes/no", "-"}:
            return
        if candidate not in seen:
            declared.append(candidate)
            seen.add(candidate)

    for line in text.splitlines():
        inline = INLINE_PATH_DECL_RE.match(line)
        if inline and inline.group("label").lower() == label_lower:
            for token in re.split(r"[,\s]+", inline.group("value").strip()):
                if token:
                    add_candidate(token)

    for section_line in section_lines(text, [f"{label_lower} paths", f"{label_lower} path"]):
        stripped = section_line.strip()
        if not stripped or stripped.startswith("```"):
            continue

        stripped = re.sub(r"^(?:[-*+]\s*|\d+[.)]\s*)", "", stripped).strip()
        if stripped.lower().startswith(f"{label_lower} paths:"):
            stripped = stripped.split(":", 1)[1].strip()

        for token in re.split(r"[,\s]+", stripped):
            if token:
                add_candidate(token)

    return declared


def path_matches(path: str, patterns: list[str]) -> bool:
    """Return True when a path matches any glob pattern."""
    path_posix = PurePosixPath(path)
    for pattern in patterns:
        try:
            if path_posix.match(pattern):
                return True
        except ValueError:
            pass
        if fnmatch.fnmatchcase(path, pattern):
            return True
    return False


def git_changed_files(base: str) -> tuple[list[ChangedFile], str | None]:
    """Return changed files since base and an optional error message."""
    seen: set[tuple[str, str, str | None]] = set()

    try:
        status_result = subprocess.run(
            [
                "git",
                "diff",
                "--name-status",
                "--diff-filter=ACMRTUXBD",
                base,
            ],
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        stderr = ""
        if isinstance(exc, subprocess.CalledProcessError):
            stderr = exc.stderr.strip()
        message = "unable to inspect git diff"
        if stderr:
            message = f"{message}: {stderr}"
        return [], message

    changed_files: list[ChangedFile] = []

    for line in status_result.stdout.splitlines():
        if not line.strip():
            continue

        parts = line.split("\t")
        status = parts[0].strip()
        if status.startswith(("R", "C")) and len(parts) >= 3:
            old_path = parts[1].strip()
            path = parts[2].strip()
        else:
            old_path = None
            path = parts[-1].strip()

        key = (status, path, old_path)
        if key in seen:
            continue
        seen.add(key)
        changed_files.append(ChangedFile(status=status, path=path, old_path=old_path))

    try:
        untracked_result = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        stderr = ""
        if isinstance(exc, subprocess.CalledProcessError):
            stderr = exc.stderr.strip()
        message = "unable to inspect untracked files"
        if stderr:
            message = f"{message}: {stderr}"
        return [], message

    for line in untracked_result.stdout.splitlines():
        path = line.strip()
        if not path:
            continue
        key = ("A", path, None)
        if key in seen:
            continue
        seen.add(key)
        changed_files.append(ChangedFile(status="A", path=path))

    return changed_files, None


def parse_verify_status(verify_text: str) -> tuple[str | None, list[str]]:
    """Return the verify gate status plus section lookup errors."""
    section = section_lines(verify_text, ["verify gate"])
    errors: list[str] = []

    if not section:
        errors.append("missing verify gate section")
        return None, errors

    section_text = "\n".join(section)
    match = VERIFY_STATUS_RE.search(section_text)
    if not match:
        errors.append("missing valid verify gate status")
        return None, errors

    return match.group(1), errors


def evaluate(args: argparse.Namespace) -> Result:
    """Compute the gate outcome."""
    checks: list[Check] = []
    failures: list[str] = []
    review_required: list[str] = []

    spec_path = Path(args.spec)
    verify_path = Path(args.verify)

    spec_text = spec_path.read_text(encoding="utf-8") if spec_path.is_file() else None
    verify_text = verify_path.read_text(encoding="utf-8") if verify_path.is_file() else None

    if spec_text is None:
        checks.append(
            Check(
                name="spec",
                status=STATUS_REVIEW,
                details=f"{spec_path} not found; treating spec evidence as incomplete.",
            )
        )
        review_required.append(f"missing SPEC.md: {spec_path}")
    else:
        missing_concepts: list[str] = []
        if not concept_present(spec_text, ["compatibility seams"]):
            missing_concepts.append("compatibility seams")
        if not concept_present(spec_text, ["invalid if", "invalid-if", "invalidation constraints"]):
            missing_concepts.append("invalid-if constraints")

        if missing_concepts:
            checks.append(
                Check(
                    name="spec",
                    status=STATUS_REVIEW,
                    details="missing concepts: " + ", ".join(missing_concepts),
                )
            )
            review_required.append(f"SPEC.md missing concepts: {', '.join(missing_concepts)}")
        else:
            checks.append(
                Check(
                    name="spec",
                    status=STATUS_PASS,
                    details="compatibility seams and invalid-if constraints detected.",
                )
            )

    declared_source = "\n".join(part for part in [spec_text, verify_text] if part)
    forbidden_patterns = extract_declared_paths(declared_source, "forbidden")
    protected_patterns = extract_declared_paths(declared_source, "protected")

    if verify_text is None:
        checks.append(
            Check(
                name="verify",
                status=STATUS_FAIL,
                details=f"{verify_path} not found.",
            )
        )
        failures.append(f"missing VERIFY.md: {verify_path}")
    else:
        verify_status, verify_errors = parse_verify_status(verify_text)
        if verify_errors:
            checks.append(
                Check(
                    name="verify",
                    status=STATUS_FAIL,
                    details=verify_errors[0],
                )
            )
            failures.extend(f"VERIFY.md {error}" for error in verify_errors)
        else:
            assert verify_status is not None
            if verify_status == STATUS_PASS:
                checks.append(Check(name="verify", status=STATUS_PASS, details="verify gate status PASS."))
            elif verify_status == STATUS_REVIEW:
                checks.append(
                    Check(
                        name="verify",
                        status=STATUS_REVIEW,
                        details="verify gate status REVIEW_REQUIRED.",
                    )
                )
                review_required.append("VERIFY.md requests REVIEW_REQUIRED")
            else:
                checks.append(Check(name="verify", status=STATUS_FAIL, details="verify gate status FAIL."))
                failures.append("VERIFY.md status is FAIL")

    changed_files, diff_error = git_changed_files(args.base)
    if diff_error is not None:
        checks.append(Check(name="diff", status=STATUS_FAIL, details=diff_error))
        failures.append(diff_error)
        changed_files = []
        changed_file_statuses: list[ChangedFile] = []
    else:
        changed_file_statuses = changed_files

        def change_paths(change: ChangedFile) -> list[str]:
            paths = [change.path]
            if change.old_path:
                paths.append(change.old_path)
            return paths

        touched_forbidden = [
            change
            for change in changed_file_statuses
            if any(path_matches(path, forbidden_patterns) for path in change_paths(change))
        ]
        touched_protected = [
            change
            for change in changed_file_statuses
            if any(path_matches(path, protected_patterns) for path in change_paths(change))
        ]
        touched_tests = [
            change
            for change in changed_file_statuses
            if any(path_matches(path, DEFAULT_TEST_PATTERNS) for path in change_paths(change))
        ]
        touched_fixtures = [
            change
            for change in changed_file_statuses
            if any(path_matches(path, DEFAULT_FIXTURE_PATTERNS) for path in change_paths(change))
        ]
        touched_dependencies = [
            change
            for change in changed_file_statuses
            if any(path_matches(path, DEFAULT_DEPENDENCY_PATTERNS) for path in change_paths(change))
        ]

        if touched_forbidden:
            failures.append("forbidden path touched: " + ", ".join(change.path for change in touched_forbidden))
        if touched_protected:
            review_required.append("protected path touched: " + ", ".join(change.path for change in touched_protected))
        if touched_tests:
            review_required.append("tests changed: " + ", ".join(change.path for change in touched_tests))
        if touched_fixtures:
            review_required.append("fixture/data changed: " + ", ".join(change.path for change in touched_fixtures))
        if touched_dependencies:
            review_required.append(
                "dependencies changed: " + ", ".join(change.path for change in touched_dependencies)
            )

        diff_details: list[str] = []
        if touched_forbidden:
            diff_details.append("forbidden path(s) touched: " + ", ".join(change.path for change in touched_forbidden))
        if touched_protected:
            diff_details.append("protected path(s) touched: " + ", ".join(change.path for change in touched_protected))
        if touched_tests:
            diff_details.append("test file(s) touched: " + ", ".join(change.path for change in touched_tests))
        if touched_fixtures:
            diff_details.append("fixture/data file(s) touched: " + ", ".join(change.path for change in touched_fixtures))
        if touched_dependencies:
            diff_details.append(
                "dependency file(s) touched: " + ", ".join(change.path for change in touched_dependencies)
            )
        if not diff_details:
            diff_details.append("no diff guards triggered.")

        diff_status = STATUS_PASS
        if touched_forbidden:
            diff_status = STATUS_FAIL
        elif touched_protected or touched_tests or touched_fixtures or touched_dependencies:
            diff_status = STATUS_REVIEW

        checks.append(Check(name="diff", status=diff_status, details="; ".join(diff_details)))

    if failures:
        status = STATUS_FAIL
    elif review_required:
        status = STATUS_REVIEW
    else:
        status = STATUS_PASS

    exit_code_policy = (
        "0 on PASS and REVIEW_REQUIRED; nonzero on FAIL; --strict-review makes REVIEW_REQUIRED nonzero"
    )

    return Result(
        status=status,
        checks=checks,
        failures=failures,
        review_required=review_required,
        changed_files=[change.path for change in changed_file_statuses],
        changed_file_statuses=changed_file_statuses,
        exit_code_policy=exit_code_policy,
    )


def emit_text(result: Result) -> None:
    """Print the human-readable gate summary."""
    print(f"VERIFY GATE: {result.status}")
    for check in result.checks:
        print(f"{check.name.capitalize()}: {check.status} - {check.details}")

    if result.changed_files:
        print("Changed files:")
        for change in result.changed_file_statuses:
            if change.old_path and change.old_path != change.path:
                print(f"- {change.status} {change.old_path} -> {change.path}")
            else:
                print(f"- {change.status} {change.path}")
    else:
        print("Changed files: none")

    if result.failures:
        print("Failures:")
        for failure in result.failures:
            print(f"- {failure}")

    if result.review_required:
        print("Review required:")
        for reason in result.review_required:
            print(f"- {reason}")


def emit_json(result: Result) -> None:
    """Print the machine-readable gate summary."""
    payload = {
        "status": result.status,
        "checks": [check.__dict__ for check in result.checks],
        "failures": result.failures,
        "review_required": result.review_required,
        "changed_files": result.changed_files,
        "changed_file_statuses": [change.__dict__ for change in result.changed_file_statuses],
        "exit_code_policy": result.exit_code_policy,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


def exit_code(result: Result, strict_review: bool) -> int:
    """Convert the gate result to a process exit code."""
    if result.status == STATUS_FAIL:
        return 1
    if result.status == STATUS_REVIEW and strict_review:
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    """Entry point."""
    args = parse_args(argv)
    result = evaluate(args)

    if args.format == "json":
        emit_json(result)
    else:
        emit_text(result)

    return exit_code(result, args.strict_review)


if __name__ == "__main__":
    raise SystemExit(main())
