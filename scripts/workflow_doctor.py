#!/usr/bin/env python3
"""Diagnose workflow artifact state without modifying the repository."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]
VERIFY_GATE = ROOT / "scripts" / "verify_gate.py"
HANDOFF_FRESHNESS = ROOT / "skills" / "handoff" / "scripts" / "handoff_freshness.py"
VALID_STATUSES = {"PASS", "FAIL", "REVIEW_REQUIRED"}
PLACEHOLDERS = {
    "",
    "-",
    "_tbd_",
    "tbd",
    "none",
    "n/a",
    "yes/no",
    "pass | fail | review_required",
}
HEADING_RE = re.compile(r"^(?P<marks>#{1,6})\s+(?P<title>.+?)\s*$")
VERIFY_STATUS_RE = re.compile(
    r"(?im)^\s*Status\s*:\s*(PASS|FAIL|REVIEW_REQUIRED)\s*$"
)
FIELD_RE = re.compile(r"^\s*(?:[-*+]\s*)?(?P<label>[^:]+):\s*(?P<value>.*)\s*$")


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    details: tuple[str, ...]


@dataclass(frozen=True)
class Diagnosis:
    status: str
    checks: tuple[Check, ...]
    next_move: str
    trusted_next_task: str | None
    changed_files: tuple[str, ...]


@dataclass(frozen=True)
class RuntimeResult:
    status: str
    details: tuple[str, ...]
    changed_files: tuple[str, ...] = ()


def normalize(value: str) -> str:
    value = value.strip().strip("`").strip()
    return re.sub(r"\s+", " ", value)


def meaningful(value: str) -> bool:
    raw = value.strip()
    if len(raw) > 2 and raw.startswith("_") and raw.endswith("_"):
        return False
    normalized = normalize(value).lower()
    return bool(normalized and normalized not in PLACEHOLDERS and "_tbd_" not in normalized)


def section(text: str, name: str) -> str:
    lines = text.splitlines()
    target = name.strip().lower()
    start: int | None = None
    level = 0
    for index, line in enumerate(lines):
        match = HEADING_RE.match(line.strip())
        if match and match.group("title").strip().lower() == target:
            start = index + 1
            level = len(match.group("marks"))
            break
    if start is None:
        return ""
    collected: list[str] = []
    for line in lines[start:]:
        match = HEADING_RE.match(line.strip())
        if match and len(match.group("marks")) <= level:
            break
        collected.append(line)
    return "\n".join(collected).strip()


def meaningful_lines(block: str) -> list[str]:
    values: list[str] = []
    for line in block.splitlines():
        stripped = re.sub(r"^\s*[-*+]\s+", "", line).strip()
        if meaningful(stripped):
            values.append(normalize(stripped))
    return values


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


def read_text(root: Path, relative: Path) -> str | None:
    try:
        return (root / relative).read_text(encoding="utf-8")
    except FileNotFoundError:
        return None


def inspect_spec(text: str | None) -> Check:
    if text is None:
        return Check("SPEC", "MISSING", ("SPEC.md is not present",))
    objective = meaningful_lines(section(text, "Objective"))
    criteria = meaningful_lines(section(text, "Acceptance criteria"))
    missing: list[str] = []
    if not objective:
        missing.append("meaningful Objective")
    if not criteria:
        missing.append("meaningful Acceptance criteria")
    if missing:
        return Check("SPEC", "INCOMPLETE", tuple(f"missing {item}" for item in missing))
    return Check(
        "SPEC",
        "READY",
        (objective[0], f"{len(criteria)} acceptance criterion/criteria"),
    )


def inspect_scope(text: str | None) -> Check:
    if text is None:
        return Check("SCOPE", "NOT_PRESENT", ("optional scope artifact not present",))
    required = {
        "Task": first_field(text, "Task"),
        "Allowed writes": first_field(text, "Allowed writes"),
        "Forbidden": first_field(text, "Forbidden", allow_none=True),
        "Stop when": first_field(text, "Stop when"),
    }
    missing = [name for name, value in required.items() if value is None]
    if "SCOPE FREEZE" not in text.upper():
        missing.insert(0, "SCOPE FREEZE marker")
    if missing:
        return Check(
            "SCOPE",
            "INCOMPLETE",
            tuple(f"missing {item}" for item in missing),
        )
    return Check(
        "SCOPE",
        "READY",
        tuple(f"{name}: {value}" for name, value in required.items()),
    )


def recorded_verify_status(text: str | None) -> str:
    if text is None:
        return "MISSING"
    block = section(text, "Verify gate") or text
    match = VERIFY_STATUS_RE.search(block)
    return match.group(1) if match else "INCOMPLETE"


def inspect_verify(text: str | None) -> Check:
    status = recorded_verify_status(text)
    if status == "MISSING":
        return Check("VERIFY", "MISSING", ("VERIFY.md is not present",))
    if status == "INCOMPLETE":
        return Check("VERIFY", "INCOMPLETE", ("recorded verify status is missing",))
    assert status in VALID_STATUSES
    details: list[str] = [f"recorded status: {status}"]
    if text is not None:
        remaining = first_field(
            text,
            "Remaining unverified risks",
            "Remaining uncertainty",
        )
        if remaining:
            details.append(f"remaining uncertainty: {remaining}")
    return Check("VERIFY", status, tuple(details))


def run_verify_gate(
    root: Path,
    base: str | None,
    spec: Path,
    verify: Path,
    script: Path = VERIFY_GATE,
) -> RuntimeResult:
    if base is None:
        return RuntimeResult(
            "REVIEW_REQUIRED",
            ("deterministic verify gate not run; supply --base",),
        )
    if not script.is_file():
        return RuntimeResult(
            "REVIEW_REQUIRED",
            (f"verify gate unavailable: {script}",),
        )
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--base",
            base,
            "--spec",
            str(spec),
            "--verify",
            str(verify),
            "--format",
            "json",
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        detail = normalize(result.stderr or result.stdout or "no output")
        return RuntimeResult(
            "REVIEW_REQUIRED",
            (f"verify gate output could not be parsed: {detail}",),
        )
    status = payload.get("status")
    if status not in VALID_STATUSES:
        return RuntimeResult(
            "REVIEW_REQUIRED",
            ("verify gate returned an unknown status",),
        )
    details: list[str] = []
    for key in ("failures", "review_required"):
        values = payload.get(key, [])
        if isinstance(values, list):
            details.extend(
                normalize(str(value))
                for value in values
                if meaningful(str(value))
            )
    if not details:
        details.append("deterministic gate completed")
    changed = payload.get("changed_files", [])
    changed_files = (
        tuple(str(value) for value in changed)
        if isinstance(changed, list)
        else ()
    )
    return RuntimeResult(status, tuple(details), changed_files)


def run_handoff_freshness(
    root: Path,
    handoff: Path,
    script: Path = HANDOFF_FRESHNESS,
) -> RuntimeResult:
    if not (root / handoff).is_file():
        return RuntimeResult("NOT_PRESENT", ("optional handoff not present",))
    if not script.is_file():
        return RuntimeResult(
            "REVIEW_REQUIRED",
            (f"handoff freshness guard unavailable: {script}",),
        )
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "check",
            "--root",
            str(root),
            "--handoff",
            str(handoff),
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    output = "\n".join(
        part for part in (result.stdout, result.stderr) if part
    ).strip()
    if "HANDOFF FRESHNESS: PASS" in output:
        status = "PASS"
    elif "HANDOFF FRESHNESS: STALE" in output:
        status = "STALE"
    else:
        status = "REVIEW_REQUIRED"
    details = tuple(
        normalize(line.lstrip("- "))
        for line in output.splitlines()[1:]
        if meaningful(line)
    ) or ("handoff freshness result recorded",)
    return RuntimeResult(status, details)


def repository_state(root: Path) -> Check:
    try:
        branch = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        dirty = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.splitlines()
    except (OSError, subprocess.CalledProcessError) as exc:
        return Check(
            "REPOSITORY",
            "REVIEW_REQUIRED",
            (f"git state unavailable: {exc}",),
        )
    details = [f"branch: {branch or '(detached)'}", f"commit: {commit}"]
    details.append(f"working tree: {'dirty' if dirty else 'clean'}")
    return Check("REPOSITORY", "READY", tuple(details))


def choose_next_move(
    spec: Check,
    scope: Check,
    verify: Check,
    gate: RuntimeResult,
    handoff: RuntimeResult,
    trusted_next_task: str | None,
) -> str:
    if spec.status == "MISSING":
        return "Create SPEC.md with a meaningful objective and acceptance criteria."
    if spec.status == "INCOMPLETE":
        return "Complete SPEC.md before implementation or verification continues."
    if scope.status == "INCOMPLETE":
        return "Reconcile the existing scope freeze before changing more files."
    if verify.status == "FAIL" or gate.status == "FAIL":
        return "Fix the failing contract and rerun verification before claiming completion."
    if verify.status in {"MISSING", "INCOMPLETE"}:
        return "Run verification and record the result in VERIFY.md."
    if gate.status == "REVIEW_REQUIRED":
        return (
            "Run the deterministic verify gate with an explicit base and resolve "
            "its review items."
        )
    if verify.status == "REVIEW_REQUIRED":
        return (
            "Resolve or explicitly accept the recorded review-required "
            "verification items."
        )
    if handoff.status in {"STALE", "REVIEW_REQUIRED"}:
        return (
            "Re-read live repository state and regenerate HANDOFF.md before "
            "resuming from it."
        )
    if trusted_next_task:
        return f"Continue with the fresh handoff task: {trusted_next_task}"
    return "Evidence is green; proceed only with the next user-approved action."


def overall_status(
    spec: Check,
    scope: Check,
    verify: Check,
    gate: RuntimeResult,
    handoff: RuntimeResult,
    repository: Check,
) -> str:
    if verify.status == "FAIL" or gate.status == "FAIL":
        return "FAIL"
    review_states = {
        spec.status,
        scope.status,
        verify.status,
        gate.status,
        handoff.status,
        repository.status,
    }
    blockers = {"MISSING", "INCOMPLETE", "REVIEW_REQUIRED", "STALE"}
    if review_states & blockers:
        return "REVIEW_REQUIRED"
    return "PASS"


def diagnose(
    root: Path,
    *,
    base: str | None,
    spec_path: Path = Path("SPEC.md"),
    scope_path: Path = Path("SCOPE.md"),
    verify_path: Path = Path("VERIFY.md"),
    handoff_path: Path = Path("HANDOFF.md"),
    verify_runner: Callable[
        [Path, str | None, Path, Path],
        RuntimeResult,
    ] = run_verify_gate,
    handoff_runner: Callable[[Path, Path], RuntimeResult] = run_handoff_freshness,
) -> Diagnosis:
    spec_text = read_text(root, spec_path)
    scope_text = read_text(root, scope_path)
    verify_text = read_text(root, verify_path)
    handoff_text = read_text(root, handoff_path)

    spec = inspect_spec(spec_text)
    scope = inspect_scope(scope_text)
    verify = inspect_verify(verify_text)
    if spec.status != "READY" or verify.status in {"MISSING", "INCOMPLETE"}:
        gate = RuntimeResult(
            "REVIEW_REQUIRED",
            (
                "deterministic verify gate not run because required artifacts "
                "are incomplete"
            ,),
        )
    else:
        gate = verify_runner(root, base, spec_path, verify_path)
    handoff = handoff_runner(root, handoff_path)
    repository = repository_state(root)

    trusted_next_task: str | None = None
    if handoff.status == "PASS" and handoff_text is not None:
        trusted_next_task = first_field(
            handoff_text,
            "Next task",
            "Next recommended task",
        )
        if trusted_next_task is None:
            tasks = meaningful_lines(section(handoff_text, "Next recommended task"))
            trusted_next_task = tasks[0] if tasks else None

    status = overall_status(spec, scope, verify, gate, handoff, repository)
    next_move = choose_next_move(
        spec,
        scope,
        verify,
        gate,
        handoff,
        trusted_next_task,
    )
    checks = (
        repository,
        spec,
        scope,
        verify,
        Check("VERIFY_GATE", gate.status, gate.details),
        Check("HANDOFF", handoff.status, handoff.details),
    )
    return Diagnosis(
        status,
        checks,
        next_move,
        trusted_next_task,
        gate.changed_files,
    )


def emit_text(result: Diagnosis) -> None:
    print(f"WORKFLOW DOCTOR: {result.status}")
    for check in result.checks:
        print(f"{check.name}: {check.status}")
        for detail in check.details:
            print(f"- {detail}")
    if result.changed_files:
        print("CHANGED FILES:")
        for path in result.changed_files:
            print(f"- {path}")
    print(f"NEXT MOVE: {result.next_move}")


def emit_json(result: Diagnosis) -> None:
    print(
        json.dumps(
            {
                "status": result.status,
                "checks": [
                    {
                        "name": check.name,
                        "status": check.status,
                        "details": list(check.details),
                    }
                    for check in result.checks
                ],
                "changed_files": list(result.changed_files),
                "trusted_next_task": result.trusted_next_task,
                "next_move": result.next_move,
            },
            indent=2,
            sort_keys=True,
        )
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--base", help="Git base passed to scripts/verify_gate.py")
    parser.add_argument("--spec", type=Path, default=Path("SPEC.md"))
    parser.add_argument("--scope", type=Path, default=Path("SCOPE.md"))
    parser.add_argument("--verify", type=Path, default=Path("VERIFY.md"))
    parser.add_argument("--handoff", type=Path, default=Path("HANDOFF.md"))
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = diagnose(
        args.root.resolve(),
        base=args.base,
        spec_path=args.spec,
        scope_path=args.scope,
        verify_path=args.verify,
        handoff_path=args.handoff,
    )
    if args.format == "json":
        emit_json(result)
    else:
        emit_text(result)
    if result.status == "PASS":
        return 0
    if result.status == "FAIL":
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
