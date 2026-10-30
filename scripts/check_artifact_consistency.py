#!/usr/bin/env python3
"""Lint durable workflow artifacts for cross-artifact contradictions."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from acceptance_coverage import evaluate as evaluate_acceptance_coverage
from check_contract_lineage import evaluate as evaluate_contract_lineage
from scope_gate import parse_scope
from verify_gate import check_compatibility_probes
from test_sensitivity import evaluate as evaluate_test_sensitivity


STATUS_PASS = "PASS"
STATUS_FAIL = "FAIL"
STATUS_REVIEW = "REVIEW_REQUIRED"
STATUS_NA = "NOT_APPLICABLE"

FIELD_RE = re.compile(
    r"^\s*(?:[-*+]\s*)?(?P<label>[^:]+):\s*(?P<value>.*?)\s*$",
    re.IGNORECASE,
)
VERIFY_STATUS_RE = re.compile(
    r"(?im)^\s*Status\s*:\s*(PASS|FAIL|REVIEW_REQUIRED)\s*$"
)
DIFF_BUDGET_REQUIREMENT_RE = re.compile(
    r"(?im)^\s*Diff\s+budget\s+requirement\s*:\s*(ENFORCED|NOT_APPLICABLE)\s*$"
)
MAX_CHANGED_FILES_RE = re.compile(
    r"(?im)^\s*[-*+]?\s*Max\s+changed\s+files\s*:\s*(\d+)\s*$"
)
PLACEHOLDERS = {
    "",
    "-",
    "_tbd_",
    "tbd",
    "n/a",
    "yes/no",
    "pass | fail | review_required",
    "pass | fail | review_required | not_present",
    "none | describe exact unresolved items",
}


@dataclass(frozen=True)
class Check:
    """One cross-artifact consistency check."""

    name: str
    status: str
    details: tuple[str, ...]


@dataclass(frozen=True)
class Result:
    """Aggregate artifact-consistency result."""

    status: str
    checks: tuple[Check, ...]
    failures: tuple[str, ...]
    review_required: tuple[str, ...]
    exit_code_policy: str


def normalize(value: str) -> str:
    """Normalize one Markdown field value."""
    value = value.strip().strip("`").strip()
    return re.sub(r"\s+", " ", value)


def meaningful(value: str) -> bool:
    """Return whether a field value is concrete rather than template text."""
    raw = value.strip()
    if len(raw) > 2 and raw.startswith("_") and raw.endswith("_"):
        return False
    normalized = normalize(value).lower()
    return bool(
        normalized
        and normalized not in PLACEHOLDERS
        and "_tbd_" not in normalized
    )


def read_text(root: Path, path: Path) -> str | None:
    """Read an artifact relative to root, returning None when absent."""
    target = path if path.is_absolute() else root / path
    try:
        return target.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None


def section(text: str, name: str) -> str:
    """Return one Markdown section body."""
    lines = text.splitlines()
    target = name.strip().lower()
    start: int | None = None
    level = 0
    heading_re = re.compile(r"^\s{0,3}(?P<marks>#{1,6})\s+(?P<title>.+?)\s*$")
    for index, line in enumerate(lines):
        match = heading_re.match(line)
        if match and match.group("title").strip().lower() == target:
            start = index + 1
            level = len(match.group("marks"))
            break
    if start is None:
        return ""

    collected: list[str] = []
    for line in lines[start:]:
        match = heading_re.match(line)
        if match and len(match.group("marks")) <= level:
            break
        collected.append(line)
    return "\n".join(collected)


def first_field(text: str, *labels: str, allow_none: bool = False) -> str | None:
    """Return the first meaningful matching Markdown field."""
    wanted = {label.strip().lower() for label in labels}
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


def recorded_verify_status(text: str | None) -> str:
    """Return recorded VERIFY.md status, including absence/incompleteness."""
    if text is None:
        return "NOT_PRESENT"
    block = section(text, "Verify gate") or text
    match = VERIFY_STATUS_RE.search(block)
    return match.group(1) if match else "INCOMPLETE"


def check_lineage(
    root: Path,
    spec_path: Path,
    plan_path: Path,
    verify_path: Path,
    handoff_path: Path,
) -> Check:
    """Compose the existing optional contract-lineage checker."""
    result = evaluate_contract_lineage(
        root,
        spec_path=spec_path,
        plan_path=plan_path,
        verify_path=verify_path,
        handoff_path=handoff_path,
    )
    details: list[str] = []
    if result.active:
        details.append(f"active contract: {result.active_contract_id}")
    else:
        details.append("contract identity inactive")
    details.extend(result.failures)
    details.extend(result.review_required)
    return Check("contract-lineage", result.status, tuple(details))


def check_acceptance_coverage(spec_text: str | None, verify_text: str | None) -> Check:
    """Compose opt-in SPEC acceptance-ID to VERIFY evidence coverage."""
    result = evaluate_acceptance_coverage(spec_text or "", verify_text or "")
    if not result.active:
        return Check(
            "acceptance-coverage",
            STATUS_NA,
            ("SPEC acceptance criteria do not opt into AC-* evidence coverage.",),
        )
    details = [
        f"{row.criterion}: {row.status}; checks: {', '.join(row.checks) or 'none'}"
        for row in result.rows
    ]
    details.extend(result.warnings)
    return Check("acceptance-coverage", result.status, tuple(details))


def check_compatibility(spec_text: str | None, verify_text: str | None) -> Check:
    """Compose the existing SPEC-to-VERIFY compatibility probe contract."""
    result = check_compatibility_probes(spec_text, verify_text)
    if result is None:
        return Check(
            "compatibility-evidence",
            STATUS_NA,
            ("SPEC does not opt into the compatibility probe contract.",),
        )
    return Check("compatibility-evidence", result.status, (result.details,))


def check_test_sensitivity(spec_text: str | None, verify_text: str | None) -> Check:
    """Compose the optional SPEC-to-VERIFY test-sensitivity contract."""
    result = evaluate_test_sensitivity(spec_text, verify_text)
    if not result.active:
        return Check(
            "test-sensitivity",
            STATUS_NA,
            ("SPEC does not opt into the test-sensitivity contract.",),
        )
    if result.status == STATUS_PASS:
        return Check(
            "test-sensitivity",
            STATUS_PASS,
            (f"{len(result.records)} required sensitivity probe(s) killed and restored.",),
        )
    return Check("test-sensitivity", STATUS_REVIEW, result.review_required)


def spec_diff_budget(spec_text: str | None) -> tuple[str, int | None]:
    """Return diff-budget requirement plus max changed files."""
    if spec_text is None:
        return STATUS_NA, None
    block = section(spec_text, "Implementation diff budget")
    if not block:
        return STATUS_NA, None
    requirement = DIFF_BUDGET_REQUIREMENT_RE.search(block)
    if requirement is None:
        return "INCOMPLETE", None
    if requirement.group(1) == "NOT_APPLICABLE":
        return STATUS_NA, None
    max_files = MAX_CHANGED_FILES_RE.search(block)
    return "ENFORCED", int(max_files.group(1)) if max_files else None


def check_spec_scope_budget(spec_text: str | None, scope_text: str | None) -> Check:
    """Check the remaining SPEC-to-SCOPE changed-file budget seam."""
    requirement, spec_max = spec_diff_budget(spec_text)
    if requirement == STATUS_NA:
        return Check(
            "spec-scope-budget",
            STATUS_NA,
            ("SPEC does not enforce an implementation diff budget.",),
        )
    if requirement == "INCOMPLETE":
        return Check(
            "spec-scope-budget",
            STATUS_REVIEW,
            ("SPEC diff-budget requirement is unresolved; alignment cannot be established.",),
        )
    if spec_max is None:
        return Check(
            "spec-scope-budget",
            STATUS_REVIEW,
            ("SPEC enforces a diff budget but Max changed files is missing.",),
        )
    if scope_text is None:
        return Check(
            "spec-scope-budget",
            STATUS_NA,
            ("SCOPE.md is absent; no hard scope file cap exists to compare.",),
        )

    scope, errors = parse_scope(scope_text)
    if scope is None or errors:
        return Check(
            "spec-scope-budget",
            STATUS_REVIEW,
            ("SCOPE.md cannot be parsed for budget alignment: " + "; ".join(errors),),
        )
    if scope.max_files_changed is None:
        return Check(
            "spec-scope-budget",
            STATUS_NA,
            ("SCOPE.md has no Max files changed cap to compare with SPEC.",),
        )
    if scope.max_files_changed > spec_max:
        return Check(
            "spec-scope-budget",
            STATUS_REVIEW,
            (
                "SCOPE.md hard file cap exceeds the SPEC implementation budget: "
                f"{scope.max_files_changed} > {spec_max}.",
            ),
        )
    return Check(
        "spec-scope-budget",
        STATUS_PASS,
        (
            f"SCOPE.md hard file cap {scope.max_files_changed} is within "
            f"SPEC max changed files {spec_max}.",
        ),
    )


def scope_gate_record(verify_text: str | None) -> str | None:
    """Extract the artifact-recorded scope-gate status."""
    if verify_text is None:
        return None
    raw = first_field(verify_text, "Scope gate")
    if raw is None:
        return None
    match = re.match(r"^(PASS|FAIL|REVIEW_REQUIRED|NOT_APPLICABLE)\b", raw, re.I)
    return match.group(1).upper() if match else "INCOMPLETE"


def check_scope_verify(scope_text: str | None, verify_text: str | None) -> Check:
    """Check whether VERIFY.md's scope-gate applicability matches SCOPE.md."""
    recorded = scope_gate_record(verify_text)
    if scope_text is None:
        if recorded in {None, "NOT_APPLICABLE"}:
            return Check(
                "scope-verify",
                STATUS_NA,
                ("No persisted scope contract requires a recorded scope-gate result.",),
            )
        return Check(
            "scope-verify",
            STATUS_REVIEW,
            (
                f"VERIFY.md records Scope gate: {recorded}, but SCOPE.md is absent.",
            ),
        )

    if verify_text is None:
        return Check(
            "scope-verify",
            STATUS_NA,
            ("VERIFY.md is not present yet; no downstream scope result to compare.",),
        )
    if recorded is None:
        return Check(
            "scope-verify",
            STATUS_REVIEW,
            ("SCOPE.md exists but VERIFY.md does not record Scope gate status.",),
        )
    if recorded == "INCOMPLETE":
        return Check(
            "scope-verify",
            STATUS_REVIEW,
            ("VERIFY.md Scope gate status is not a recognized deterministic status.",),
        )
    if recorded == "NOT_APPLICABLE":
        return Check(
            "scope-verify",
            STATUS_REVIEW,
            ("VERIFY.md marks Scope gate NOT_APPLICABLE even though SCOPE.md exists.",),
        )
    return Check(
        "scope-verify",
        STATUS_PASS,
        (f"SCOPE.md exists and VERIFY.md records Scope gate: {recorded}.",),
    )


def handoff_verify_status(handoff_text: str) -> str | None:
    """Extract the handoff's expected verify-gate status."""
    raw = first_field(handoff_text, "Verify gate status")
    if raw is None:
        return None
    match = re.match(r"^(PASS|FAIL|REVIEW_REQUIRED|NOT_PRESENT)\b", raw, re.I)
    return match.group(1).upper() if match else "INCOMPLETE"


def check_verify_handoff(verify_text: str | None, handoff_text: str | None) -> Check:
    """Check VERIFY.md status and review posture against HANDOFF.md."""
    if handoff_text is None:
        return Check(
            "verify-handoff",
            STATUS_NA,
            ("HANDOFF.md is absent; no continuation state to compare.",),
        )

    live = recorded_verify_status(verify_text)
    expected = handoff_verify_status(handoff_text)
    problems: list[str] = []

    if expected is None:
        problems.append("HANDOFF.md does not record Verify gate status.")
    elif expected == "INCOMPLETE":
        problems.append("HANDOFF.md Verify gate status is not a recognized status.")
    elif live == "INCOMPLETE":
        problems.append("VERIFY.md status is incomplete.")
    elif expected != live:
        problems.append(
            f"verify status mismatch: HANDOFF={expected}, VERIFY={live}."
        )

    review_items = first_field(
        handoff_text,
        "Review-required items",
        allow_none=True,
    )
    if review_items is None:
        problems.append("HANDOFF.md does not record Review-required items.")
    elif review_items.lower() == "none" and live == STATUS_REVIEW:
        problems.append(
            "HANDOFF.md says Review-required items: none while VERIFY.md is REVIEW_REQUIRED."
        )
    elif review_items.lower() != "none" and live == STATUS_PASS:
        problems.append(
            "HANDOFF.md carries review-required items while VERIFY.md is PASS."
        )

    if problems:
        return Check("verify-handoff", STATUS_REVIEW, tuple(problems))
    return Check(
        "verify-handoff",
        STATUS_PASS,
        (f"HANDOFF verify state matches VERIFY.md: {live}.",),
    )


def evaluate(
    root: Path,
    *,
    spec_path: Path = Path("SPEC.md"),
    plan_path: Path = Path("PLAN.md"),
    scope_path: Path = Path("SCOPE.md"),
    verify_path: Path = Path("VERIFY.md"),
    handoff_path: Path = Path("HANDOFF.md"),
) -> Result:
    """Evaluate cross-artifact consistency without modifying artifacts."""
    root = root.expanduser().resolve()
    spec_text = read_text(root, spec_path)
    scope_text = read_text(root, scope_path)
    verify_text = read_text(root, verify_path)
    handoff_text = read_text(root, handoff_path)

    checks = (
        check_lineage(root, spec_path, plan_path, verify_path, handoff_path),
        check_acceptance_coverage(spec_text, verify_text),
        check_compatibility(spec_text, verify_text),
        check_test_sensitivity(spec_text, verify_text),
        check_spec_scope_budget(spec_text, scope_text),
        check_scope_verify(scope_text, verify_text),
        check_verify_handoff(verify_text, handoff_text),
    )

    failures = tuple(
        f"{check.name}: {detail}"
        for check in checks
        if check.status == STATUS_FAIL
        for detail in check.details
    )
    reviews = tuple(
        f"{check.name}: {detail}"
        for check in checks
        if check.status == STATUS_REVIEW
        for detail in check.details
    )
    status = (
        STATUS_FAIL
        if failures
        else STATUS_REVIEW
        if reviews
        else STATUS_PASS
    )
    return Result(
        status=status,
        checks=checks,
        failures=failures,
        review_required=reviews,
        exit_code_policy="PASS=0; FAIL=1; REVIEW_REQUIRED=2",
    )


def emit_text(result: Result) -> None:
    """Print a concise human-readable consistency report."""
    print(f"ARTIFACT CONSISTENCY: {result.status}")
    for check in result.checks:
        print(f"{check.name}: {check.status}")
        for detail in check.details:
            print(f"- {detail}")
    if result.failures:
        print("Failures:")
        for item in result.failures:
            print(f"- {item}")
    if result.review_required:
        print("Review required:")
        for item in result.review_required:
            print(f"- {item}")


def emit_json(result: Result) -> None:
    """Print the machine-readable consistency report."""
    print(json.dumps(asdict(result), indent=2, sort_keys=True))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--spec", type=Path, default=Path("SPEC.md"))
    parser.add_argument("--plan", type=Path, default=Path("PLAN.md"))
    parser.add_argument("--scope", type=Path, default=Path("SCOPE.md"))
    parser.add_argument("--verify", type=Path, default=Path("VERIFY.md"))
    parser.add_argument("--handoff", type=Path, default=Path("HANDOFF.md"))
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = evaluate(
        args.root,
        spec_path=args.spec,
        plan_path=args.plan,
        scope_path=args.scope,
        verify_path=args.verify,
        handoff_path=args.handoff,
    )
    if args.format == "json":
        emit_json(result)
    else:
        emit_text(result)
    return {STATUS_PASS: 0, STATUS_FAIL: 1, STATUS_REVIEW: 2}[result.status]


if __name__ == "__main__":
    raise SystemExit(main())
