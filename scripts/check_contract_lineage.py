#!/usr/bin/env python3
"""Check optional execution-contract identity across durable workflow artifacts."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

STATUS_PASS = "PASS"
STATUS_FAIL = "FAIL"
STATUS_REVIEW = "REVIEW_REQUIRED"

PLACEHOLDERS = {"", "-", "_tbd_", "tbd", "n/a", "na", "unknown"}
NONE_VALUES = {"none", "_none_"}
FIELD_RE = re.compile(
    r"^\s*(?:[-*+]\s*)?(?P<label>[A-Za-z][A-Za-z0-9 /_-]*?):\s*(?P<value>.*?)\s*$"
)

CONTRACT_LABELS = {"contract id", "active contract id"}
PARENT_LABELS = {
    "parent",
    "parent contract id",
    "supersedes contract id",
    "supersedes",
}
BASE_LABELS = {"base commit", "contract base commit"}
REPLAN_LABELS = {"replan reason"}


@dataclass(frozen=True)
class ArtifactState:
    name: str
    path: str
    present: bool
    contract_ids: tuple[str, ...]


@dataclass(frozen=True)
class Result:
    status: str
    active: bool
    active_contract_id: str | None
    parent_contract_id: str | None
    base_commit: str | None
    failures: tuple[str, ...]
    review_required: tuple[str, ...]
    artifacts: tuple[ArtifactState, ...]


def normalize(value: str) -> str:
    value = value.strip().strip("`").strip()
    return re.sub(r"\s+", " ", value)


def canonical(value: str) -> str:
    return normalize(value).lower()


def meaningful(value: str) -> bool:
    raw = value.strip()
    lowered = canonical(value)
    if len(raw) > 2 and raw.startswith("_") and raw.endswith("_"):
        return False
    return bool(
        lowered
        and lowered not in PLACEHOLDERS
        and lowered not in NONE_VALUES
    )


def split_fields(text: str) -> list[tuple[str, str]]:
    fields: list[tuple[str, str]] = []
    for raw_line in text.splitlines():
        for fragment in raw_line.split("|"):
            match = FIELD_RE.match(fragment)
            if not match:
                continue
            fields.append(
                (
                    canonical(match.group("label")),
                    normalize(match.group("value")),
                )
            )
    return fields


def values_for(text: str, labels: set[str]) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for label, value in split_fields(text):
        if label not in labels or not meaningful(value):
            continue
        if value not in seen:
            seen.add(value)
            values.append(value)
    return values


def optional_value(
    text: str,
    labels: set[str],
    *,
    allow_none: bool = False,
    allow_unknown: bool = False,
) -> str | None:
    for label, value in split_fields(text):
        if label not in labels:
            continue
        lowered = canonical(value)
        if allow_none and lowered in NONE_VALUES:
            return None
        if allow_unknown and lowered == "unknown":
            return "unknown"
        if meaningful(value):
            return value
    return None


def read_text(root: Path, path: Path) -> str | None:
    target = path if path.is_absolute() else root / path
    try:
        return target.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None


def artifact_state(
    name: str,
    path: Path,
    text: str | None,
) -> ArtifactState:
    ids = (
        tuple(values_for(text, CONTRACT_LABELS))
        if text is not None
        else ()
    )
    return ArtifactState(
        name=name,
        path=str(path),
        present=text is not None,
        contract_ids=ids,
    )


def git_check(root: Path, base: str) -> tuple[str, str | None]:
    """Establish that the recorded base resolves and is an ancestor of HEAD."""
    try:
        resolved = subprocess.run(
            ["git", "rev-parse", "--verify", f"{base}^{{commit}}"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return STATUS_REVIEW, None

    if resolved.returncode != 0 or not resolved.stdout.strip():
        return STATUS_REVIEW, None

    sha = resolved.stdout.strip()
    ancestry = subprocess.run(
        ["git", "merge-base", "--is-ancestor", sha, "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if ancestry.returncode == 0:
        return STATUS_PASS, sha
    return STATUS_REVIEW, sha


def evaluate(
    root: Path,
    *,
    spec_path: Path,
    plan_path: Path,
    verify_path: Path,
    handoff_path: Path,
    git_checker: Callable[[Path, str], tuple[str, str | None]] = git_check,
) -> Result:
    texts = {
        "SPEC": read_text(root, spec_path),
        "PLAN": read_text(root, plan_path),
        "VERIFY": read_text(root, verify_path),
        "HANDOFF": read_text(root, handoff_path),
    }
    paths = {
        "SPEC": spec_path,
        "PLAN": plan_path,
        "VERIFY": verify_path,
        "HANDOFF": handoff_path,
    }
    artifacts = tuple(
        artifact_state(name, paths[name], texts[name])
        for name in ("SPEC", "PLAN", "VERIFY", "HANDOFF")
    )

    failures: list[str] = []
    reviews: list[str] = []
    spec_text = texts["SPEC"] or ""
    spec_ids = values_for(spec_text, CONTRACT_LABELS)
    downstream_ids = [
        value
        for state in artifacts[1:]
        for value in state.contract_ids
    ]

    if len(spec_ids) > 1:
        failures.append(
            "SPEC declares multiple contract IDs: " + ", ".join(spec_ids)
        )
        active_id = spec_ids[0]
    else:
        active_id = spec_ids[0] if spec_ids else None

    if active_id is None:
        spec_identity_fields = values_for(
            spec_text,
            PARENT_LABELS | BASE_LABELS | REPLAN_LABELS,
        )
        if spec_identity_fields:
            reviews.append(
                "SPEC has contract identity metadata but no active Contract ID"
            )
        if downstream_ids:
            reviews.append(
                "downstream artifact declares Contract ID but SPEC has no active Contract ID"
            )
        status = (
            STATUS_FAIL
            if failures
            else STATUS_REVIEW
            if reviews
            else STATUS_PASS
        )
        return Result(
            status,
            False,
            None,
            None,
            None,
            tuple(failures),
            tuple(reviews),
            artifacts,
        )

    parent_id = optional_value(spec_text, PARENT_LABELS, allow_none=True)
    base_commit = optional_value(
        spec_text,
        BASE_LABELS,
        allow_unknown=True,
    )
    replan_reason = optional_value(
        spec_text,
        REPLAN_LABELS,
        allow_none=True,
    )

    if parent_id == active_id:
        failures.append("active Contract ID cannot be its own parent")
    if parent_id and not replan_reason:
        reviews.append(
            "replanned contract has a parent but no meaningful Replan reason"
        )
    if replan_reason and not parent_id:
        reviews.append(
            "Replan reason is recorded without a parent contract ID"
        )

    if base_commit is None:
        reviews.append("active contract has no Base commit")
    elif canonical(base_commit) == "unknown":
        reviews.append("active contract Base commit is unknown")
    else:
        base_status, resolved = git_checker(root, base_commit)
        if base_status != STATUS_PASS:
            reviews.append(
                "Base commit could not be established as an ancestor of HEAD: "
                + base_commit
            )
        elif resolved is None:
            reviews.append(
                f"Base commit resolved without a commit SHA: {base_commit}"
            )

    for state in artifacts[1:]:
        if not state.present:
            continue
        if not state.contract_ids:
            reviews.append(
                f"{state.name} exists but does not carry active Contract ID {active_id}"
            )
            continue
        if len(state.contract_ids) > 1:
            failures.append(
                f"{state.name} declares multiple contract IDs: "
                + ", ".join(state.contract_ids)
            )
            continue

        artifact_id = state.contract_ids[0]
        if artifact_id == active_id:
            continue
        if parent_id and artifact_id == parent_id:
            failures.append(
                f"{state.name} references parent/obsolete contract {artifact_id}; "
                f"active contract is {active_id}"
            )
        else:
            failures.append(
                f"{state.name} contract ID {artifact_id} does not match "
                f"active contract {active_id}"
            )

    status = (
        STATUS_FAIL
        if failures
        else STATUS_REVIEW
        if reviews
        else STATUS_PASS
    )
    return Result(
        status,
        True,
        active_id,
        parent_id,
        base_commit,
        tuple(failures),
        tuple(reviews),
        artifacts,
    )


def emit_text(result: Result) -> None:
    print(f"CONTRACT LINEAGE: {result.status}")
    if not result.active:
        mode = "INACTIVE" if result.status == STATUS_PASS else "UNESTABLISHED"
        print(f"MODE: {mode}")
    else:
        print(f"ACTIVE CONTRACT: {result.active_contract_id}")
        print(f"PARENT CONTRACT: {result.parent_contract_id or 'none'}")
        print(f"BASE COMMIT: {result.base_commit or 'not recorded'}")

    for artifact in result.artifacts:
        if not artifact.present:
            print(f"{artifact.name}: NOT_PRESENT")
        elif artifact.contract_ids:
            print(f"{artifact.name}: {', '.join(artifact.contract_ids)}")
        else:
            print(f"{artifact.name}: NO_CONTRACT_ID")

    for item in result.failures:
        print(f"FAIL: {item}")
    for item in result.review_required:
        print(f"REVIEW_REQUIRED: {item}")


def emit_json(result: Result) -> None:
    payload = asdict(result)
    payload["artifacts"] = [asdict(item) for item in result.artifacts]
    print(json.dumps(payload, indent=2, sort_keys=True))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--spec", type=Path, default=Path("SPEC.md"))
    parser.add_argument("--plan", type=Path, default=Path("PLAN.md"))
    parser.add_argument("--verify", type=Path, default=Path("VERIFY.md"))
    parser.add_argument("--handoff", type=Path, default=Path("HANDOFF.md"))
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = evaluate(
        args.root.expanduser().resolve(),
        spec_path=args.spec,
        plan_path=args.plan,
        verify_path=args.verify,
        handoff_path=args.handoff,
    )
    if args.format == "json":
        emit_json(result)
    else:
        emit_text(result)

    if result.status == STATUS_PASS:
        return 0
    if result.status == STATUS_FAIL:
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
