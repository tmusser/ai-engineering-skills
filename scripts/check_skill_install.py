#!/usr/bin/env python3
"""Compare installed AI Engineering Skills against their recorded install snapshot and current repo."""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from install_common import (
    InstallerError,
    SKILLS_DIR,
    assess_skill_state,
    available_skill_names,
    hash_directory,
    selected_skill_names,
)


TARGETS = {
    "claude": {
        "installer": "claude-code",
        "label": "Claude Code",
        "user_root": Path(".claude") / "skills",
        "project_root": Path(".claude") / "skills",
        "user_flag": "--claude-user",
        "project_flag": "--claude-project",
    },
    "codex": {
        "installer": "codex",
        "label": "Codex",
        "user_root": Path(".agents") / "skills",
        "project_root": Path(".agents") / "skills",
        "user_flag": "--codex-user",
        "project_flag": "--codex-project",
    },
}


@dataclass(frozen=True)
class DriftResult:
    skill: str
    status: str
    detail: str
    installed_commit: str | None
    repo_hash: str
    snapshot_hash: str | None
    installed_hash: str | None


@dataclass(frozen=True)
class InstallReport:
    status: str
    target: str
    location: str
    skill_root: str
    skills: tuple[DriftResult, ...]
    repair_command: str | None
    review_required: tuple[str, ...]


def resolve_skill_root(target: str, project_path: Path | None) -> tuple[Path, str]:
    config = TARGETS[target]
    if project_path is None:
        return Path.home() / config["user_root"], "user"

    project = project_path.expanduser().resolve()
    if not project.exists() or not project.is_dir():
        raise InstallerError(f"project path does not exist or is not a directory: {project}")
    return project / config["project_root"], "project"


def skills_to_check(only: str | None, skill_root: Path) -> list[str]:
    valid_names = available_skill_names()
    if only is not None:
        return selected_skill_names(only, valid_names)

    present = sorted(name for name in valid_names if (skill_root / name).exists())
    if not present:
        raise InstallerError(
            f"no known AI Engineering Skills skill directories found at: {skill_root}. "
            "Use --only to name skills that are expected to be installed."
        )
    return present


def classify_skill(skill_name: str, skill_root: Path, target: str) -> DriftResult:
    destination = skill_root / skill_name
    state = assess_skill_state(destination, skill_name)
    repo_hash = hash_directory(SKILLS_DIR / skill_name)

    if state.status == "absent":
        return DriftResult(
            skill_name,
            "MISSING",
            "skill is not installed at the selected target",
            None,
            repo_hash,
            None,
            None,
        )

    if state.status == "unmanaged":
        return DriftResult(
            skill_name,
            "REVIEW_REQUIRED",
            "skill exists without a trusted AI Engineering Skills manifest",
            None,
            repo_hash,
            None,
            None,
        )

    if state.status == "invalid-manifest":
        return DriftResult(
            skill_name,
            "REVIEW_REQUIRED",
            "installed manifest is missing required provenance fields or cannot be parsed",
            None,
            repo_hash,
            state.manifest_hash,
            state.current_hash,
        )

    manifest = state.manifest or {}
    expected_installer = TARGETS[target]["installer"]
    installed_with = manifest.get("installer")
    if installed_with != expected_installer:
        return DriftResult(
            skill_name,
            "REVIEW_REQUIRED",
            f"manifest installer is {installed_with!r}, expected {expected_installer!r}",
            str(manifest.get("repo_commit") or "unknown"),
            repo_hash,
            state.manifest_hash,
            state.current_hash,
        )

    installed_commit = str(manifest.get("repo_commit") or "unknown")
    if state.status == "managed-modified":
        return DriftResult(
            skill_name,
            "LOCALLY_MODIFIED",
            "installed files differ from their recorded install snapshot",
            installed_commit,
            repo_hash,
            state.manifest_hash,
            state.current_hash,
        )

    if state.status != "managed-clean":
        return DriftResult(
            skill_name,
            "REVIEW_REQUIRED",
            f"unexpected managed install state: {state.status}",
            installed_commit,
            repo_hash,
            state.manifest_hash,
            state.current_hash,
        )

    if state.manifest_hash == repo_hash:
        return DriftResult(
            skill_name,
            "CURRENT",
            "installed snapshot matches the current repository skill",
            installed_commit,
            repo_hash,
            state.manifest_hash,
            state.current_hash,
        )

    return DriftResult(
        skill_name,
        "OUTDATED",
        "installed snapshot is clean but differs from the current repository skill",
        installed_commit,
        repo_hash,
        state.manifest_hash,
        state.current_hash,
    )


def build_repair_command(
    target: str,
    location: str,
    project_path: Path | None,
    repairable: list[str],
) -> str | None:
    if not repairable:
        return None

    config = TARGETS[target]
    parts = ["python", "scripts/aes.py", "install"]
    if location == "user":
        parts.append(str(config["user_flag"]))
    else:
        assert project_path is not None
        parts.extend([str(config["project_flag"]), str(project_path.expanduser().resolve())])
    parts.extend(["--only", ",".join(repairable)])
    return " ".join(shlex.quote(part) for part in parts)


def evaluate_install(
    *,
    target: str,
    skill_root: Path,
    location: str,
    project_path: Path | None,
    skill_names: list[str],
) -> InstallReport:
    results = tuple(classify_skill(name, skill_root, target) for name in skill_names)
    statuses = {result.status for result in results}

    if "REVIEW_REQUIRED" in statuses:
        overall = "REVIEW_REQUIRED"
    elif statuses == {"CURRENT"}:
        overall = "CURRENT"
    else:
        overall = "DRIFT"

    repairable = [
        result.skill
        for result in results
        if result.status in {"MISSING", "OUTDATED"}
    ]
    review_required = tuple(
        result.skill
        for result in results
        if result.status in {"LOCALLY_MODIFIED", "REVIEW_REQUIRED"}
    )

    return InstallReport(
        status=overall,
        target=target,
        location=location,
        skill_root=str(skill_root),
        skills=results,
        repair_command=build_repair_command(
            target,
            location,
            project_path,
            repairable,
        ),
        review_required=review_required,
    )


def emit_text(report: InstallReport) -> None:
    config = TARGETS[report.target]
    print(f"SKILL INSTALL DRIFT: {report.status}")
    print(f"Target: {config['label']} ({report.location})")
    print(f"Skill root: {report.skill_root}")
    for result in report.skills:
        print(f"- {result.skill}: {result.status} — {result.detail}")
        if result.installed_commit:
            print(f"  installed from: {result.installed_commit}")
    if report.repair_command:
        print("SAFE REPAIR:")
        print(f"- {report.repair_command}")
    if report.review_required:
        print("REVIEW BEFORE REPAIR:")
        print(
            "- " + ", ".join(report.review_required)
            + " (local or untrusted state will not be overwritten automatically)"
        )


def emit_json(report: InstallReport) -> None:
    payload = asdict(report)
    payload["skills"] = [asdict(result) for result in report.skills]
    payload["review_required"] = list(report.review_required)
    print(json.dumps(payload, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", choices=sorted(TARGETS), required=True)
    parser.add_argument(
        "--project-path",
        type=Path,
        help="Check a project install instead of the default user-level install.",
    )
    parser.add_argument(
        "--only",
        help=(
            "Comma-separated skills expected to be installed. Without --only, "
            "check only known skill directories already present at the target."
        ),
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        skill_root, location = resolve_skill_root(args.target, args.project_path)
        names = skills_to_check(args.only, skill_root)
        report = evaluate_install(
            target=args.target,
            skill_root=skill_root,
            location=location,
            project_path=args.project_path,
            skill_names=names,
        )
    except InstallerError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        emit_json(report)
    else:
        emit_text(report)

    if report.status == "CURRENT":
        return 0
    if report.status == "DRIFT":
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
