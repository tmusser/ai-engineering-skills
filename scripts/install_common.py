#!/usr/bin/env python3
"""Shared installer logic for AI Engineering Skills."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills"
TEMPLATES_DIR = ROOT / "templates"
PACKAGE_NAME = "ai-engineering-skills"
VERSION_FILENAME = "AI_ENGINEERING_SKILLS_VERSION.json"


class InstallerError(Exception):
    """Raised when the installer cannot continue safely."""


@dataclass(frozen=True)
class InstallerSpec:
    """Installer-specific paths and output formatting."""

    installer_id: str
    display_name: str
    command_prefix: str
    resolve_skill_target: Callable[[argparse.Namespace], Path]
    resolve_support_root: Callable[[argparse.Namespace], Path]


@dataclass(frozen=True)
class SkillState:
    """Current state of an installed skill directory."""

    destination: Path
    exists: bool
    status: str
    manifest: dict[str, object] | None
    current_hash: str | None
    manifest_hash: str | None


@dataclass(frozen=True)
class PlannedAction:
    """One filesystem action with dry-run and real-run text."""

    dry_messages: list[str]
    run_messages: list[str]
    executor: Callable[[], None]


def add_common_arguments(parser: argparse.ArgumentParser, template_help: str) -> None:
    """Add the common CLI options shared by both installers."""
    parser.add_argument(
        "--target",
        choices=["user", "project"],
        required=True,
        help="Install to the user skill folder or to <project> skill folder.",
    )
    parser.add_argument(
        "--project-path",
        type=Path,
        help="Target project path. Required when --target project is used.",
    )
    parser.add_argument(
        "--include-templates",
        action="store_true",
        help=template_help,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be installed without creating or replacing files.",
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Back up any existing skill or template target before replacement or removal.",
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Remove installed skills instead of installing them.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Override modified or unmanaged destinations.",
    )
    parser.add_argument(
        "--only",
        help="Comma-separated list of skill directory names to install or uninstall.",
    )


def fail(message: str) -> None:
    """Raise a consistent installer error."""
    raise InstallerError(message)


def validate_repo_paths() -> None:
    """Confirm the source repository contains the expected assets."""
    if not SKILLS_DIR.is_dir():
        fail(f"skills directory not found: {SKILLS_DIR}")

    if not TEMPLATES_DIR.is_dir():
        fail(f"templates directory not found: {TEMPLATES_DIR}")


def available_skill_names() -> list[str]:
    """Return every skill directory present in the source repo."""
    names = sorted(path.name for path in SKILLS_DIR.iterdir() if path.is_dir())

    if not names:
        fail(f"no skill directories found under: {SKILLS_DIR}")

    for name in names:
        skill_file = SKILLS_DIR / name / "SKILL.md"
        if not skill_file.is_file():
            fail(f"missing SKILL.md in: {SKILLS_DIR / name}")

    return names


def resolve_project_path(args: argparse.Namespace) -> Path:
    """Validate and normalize the project path when requested."""
    if args.project_path is None:
        fail("--project-path is required when --target project is used")

    project_path = args.project_path.expanduser().resolve()

    if not project_path.exists():
        fail(f"project path does not exist: {project_path}")

    if not project_path.is_dir():
        fail(f"project path is not a directory: {project_path}")

    return project_path


def selected_skill_names(only: str | None, valid_names: list[str]) -> list[str]:
    """Parse --only and keep the selected names in user order."""
    if only is None:
        return valid_names

    requested: list[str] = []
    seen: set[str] = set()
    unknown: list[str] = []
    valid_name_set = set(valid_names)

    for raw_name in only.split(","):
        name = raw_name.strip()
        if not name:
            continue

        if name not in valid_name_set:
            unknown.append(name)
            continue

        if name not in seen:
            requested.append(name)
            seen.add(name)

    if unknown:
        valid_list = ", ".join(valid_names)
        requested_list = ", ".join(unknown)
        fail(f"unknown skill name(s): {requested_list}. Valid skills: {valid_list}")

    if not requested:
        fail("--only did not include any valid skill names")

    return requested


def utc_timestamp() -> str:
    """Return a compact UTC timestamp for backup names."""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def repo_commit() -> str:
    """Return the source repository commit hash when git is available."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown"

    commit = result.stdout.strip()
    return commit or "unknown"


def normalized_hash(value: object) -> str | None:
    """Normalize the stored content hash value."""
    if not isinstance(value, str) or not value:
        return None

    if value.startswith("sha256:"):
        return value.split(":", 1)[1]

    return value


def hash_directory(directory: Path) -> str:
    """Hash a directory tree, excluding the installed manifest file."""
    digest = hashlib.sha256()

    if not directory.exists():
        return digest.hexdigest()

    files = sorted(
        path
        for path in directory.rglob("*")
        if path.is_file() and path.name != VERSION_FILENAME
    )

    for path in files:
        relative = path.relative_to(directory).as_posix().encode("utf-8")
        digest.update(relative)
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")

    return digest.hexdigest()


def read_manifest(destination: Path) -> dict[str, object] | None:
    """Read the installed manifest if present."""
    manifest_path = destination / VERSION_FILENAME

    if not manifest_path.is_file():
        return None

    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"_invalid": True}

    if not isinstance(raw, dict):
        return {"_invalid": True}

    return raw


def assess_skill_state(destination: Path, skill_name: str) -> SkillState:
    """Determine whether a destination is managed, modified, or unmanaged."""
    if not destination.exists():
        return SkillState(destination, False, "absent", None, None, None)

    if not destination.is_dir():
        return SkillState(destination, True, "unmanaged", None, None, None)

    manifest = read_manifest(destination)

    if manifest is None:
        return SkillState(destination, True, "unmanaged", None, None, None)

    if manifest.get("_invalid"):
        return SkillState(destination, True, "invalid-manifest", manifest, None, None)

    if manifest.get("package") != PACKAGE_NAME or manifest.get("skill") != skill_name:
        return SkillState(destination, True, "unmanaged", manifest, None, None)

    current_hash = hash_directory(destination)
    manifest_hash = normalized_hash(manifest.get("content_hash"))

    if manifest_hash is None:
        return SkillState(destination, True, "invalid-manifest", manifest, current_hash, None)

    if current_hash == manifest_hash:
        return SkillState(destination, True, "managed-clean", manifest, current_hash, manifest_hash)

    return SkillState(destination, True, "managed-modified", manifest, current_hash, manifest_hash)


def write_manifest(
    destination: Path,
    *,
    installer_id: str,
    skill_name: str,
    source_path: Path,
) -> None:
    """Write a manifest into the installed skill directory."""
    manifest = {
        "schema_version": 1,
        "package": PACKAGE_NAME,
        "installer": installer_id,
        "skill": skill_name,
        "source_path": source_path.as_posix(),
        "repo_commit": repo_commit(),
        "installed_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "content_hash": f"sha256:{hash_directory(destination)}",
    }

    manifest_path = destination / VERSION_FILENAME
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def ensure_parent(path: Path) -> None:
    """Create the parent directory for a target path."""
    path.parent.mkdir(parents=True, exist_ok=True)


def remove_path(path: Path) -> None:
    """Remove a file or directory safely."""
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink(missing_ok=True)


def copy_tree(source: Path, destination: Path) -> None:
    """Copy a directory tree to a destination that does not yet exist."""
    ensure_parent(destination)
    shutil.copytree(source, destination)


def backup_destination(
    destination: Path,
    backup_root: Path,
    *,
    kind: str,
    skill_name: str | None = None,
    timestamp: str,
) -> Path:
    """Back up an existing destination into the support backup root."""
    if kind == "skill":
        if skill_name is None:
            fail("skill backups require a skill name")
        backup_path = backup_root / "skills" / f"{skill_name}-{timestamp}"
    else:
        backup_path = backup_root / f"templates-{timestamp}"

    ensure_parent(backup_path)
    if destination.is_dir() and not destination.is_symlink():
        shutil.copytree(destination, backup_path)
    else:
        shutil.copy2(destination, backup_path)
    return backup_path


def skill_backup_path(backup_root: Path, skill_name: str, timestamp: str) -> Path:
    """Return the backup path for a skill without mutating the filesystem."""
    return backup_root / "skills" / f"{skill_name}-{timestamp}"


def template_backup_path(backup_root: Path, timestamp: str) -> Path:
    """Return the backup path for templates without mutating the filesystem."""
    return backup_root / f"templates-{timestamp}"


def plan_skill_install(
    spec: InstallerSpec,
    *,
    skill_name: str,
    source: Path,
    destination: Path,
    backup_root: Path,
    dry_run: bool,
    backup: bool,
    force: bool,
) -> PlannedAction:
    """Plan a single skill installation or replacement."""
    state = assess_skill_state(destination, skill_name)
    timestamp = utc_timestamp()
    should_backup = backup and state.exists
    backup_path = skill_backup_path(backup_root, skill_name, timestamp) if should_backup else None

    if state.status == "absent":
        dry_messages = [f"Would install skill: {destination}"]
        run_messages = [f"Installed skill: {destination}"]
    elif state.status == "managed-clean":
        dry_messages = [f"Would update managed skill: {destination}"]
        run_messages = [f"Updated managed skill: {destination}"]
    elif state.status == "managed-modified":
        if not force:
            fail(
                f"refusing to overwrite locally modified skill: {destination}. "
                "Use --force to replace it."
            )
        dry_messages = [f"Would overwrite locally modified skill with --force: {destination}"]
        run_messages = [f"Overwrote locally modified skill with --force: {destination}"]
    elif state.status == "unmanaged":
        if not force:
            fail(
                f"refusing to overwrite unmanaged skill folder: {destination}. "
                "Use --force to replace it."
            )
        dry_messages = [f"Would overwrite unmanaged skill folder with --force: {destination}"]
        run_messages = [f"Overwrote unmanaged skill folder with --force: {destination}"]
    else:
        if not force:
            fail(
                f"refusing to overwrite skill with invalid manifest: {destination}. "
                "Use --force to replace it."
            )
        dry_messages = [f"Would overwrite skill with invalid manifest with --force: {destination}"]
        run_messages = [f"Overwrote skill with invalid manifest with --force: {destination}"]

    if should_backup and backup_path is not None:
        dry_messages.insert(0, f"Would back up existing skill to: {backup_path}")
        run_messages.insert(0, f"Backed up existing skill to: {backup_path}")

    def execute() -> None:
        if should_backup and backup_path is not None:
            backup_destination(
                destination,
                backup_root,
                kind="skill",
                skill_name=skill_name,
                timestamp=timestamp,
            )
        if destination.exists():
            remove_path(destination)
        copy_tree(source, destination)
        write_manifest(
            destination,
            installer_id=spec.installer_id,
            skill_name=skill_name,
            source_path=source.relative_to(ROOT),
        )

    return PlannedAction(dry_messages, run_messages, execute)


def plan_skill_uninstall(
    *,
    skill_name: str,
    destination: Path,
    backup_root: Path,
    dry_run: bool,
    backup: bool,
    force: bool,
) -> PlannedAction | None:
    """Plan a single skill removal."""
    state = assess_skill_state(destination, skill_name)
    timestamp = utc_timestamp()
    should_backup = backup and state.exists
    backup_path = skill_backup_path(backup_root, skill_name, timestamp) if should_backup else None

    if state.status == "absent":
        return None

    if state.status in {"managed-clean"}:
        dry_messages = [f"Would remove skill: {destination}"]
        run_messages = [f"Removed skill: {destination}"]
    elif state.status in {"managed-modified", "unmanaged", "invalid-manifest"}:
        if not force:
            fail(
                f"refusing to remove {state.status.replace('-', ' ')} skill folder: {destination}. "
                "Use --force to remove it."
            )
        dry_messages = [f"Would remove {state.status.replace('-', ' ')} skill folder with --force: {destination}"]
        run_messages = [f"Removed {state.status.replace('-', ' ')} skill folder with --force: {destination}"]
    else:
        fail(f"unexpected skill state for uninstall: {state.status}")

    if should_backup and backup_path is not None:
        dry_messages.insert(0, f"Would back up existing skill to: {backup_path}")
        run_messages.insert(0, f"Backed up existing skill to: {backup_path}")

    def execute() -> None:
        if should_backup and backup_path is not None:
            backup_destination(
                destination,
                backup_root,
                kind="skill",
                skill_name=skill_name,
                timestamp=timestamp,
            )
        remove_path(destination)

    return PlannedAction(dry_messages, run_messages, execute)


def plan_template_install(
    *,
    source: Path,
    destination: Path,
    backup_root: Path,
    dry_run: bool,
    backup: bool,
) -> PlannedAction:
    """Plan copying the shared templates directory."""
    timestamp = utc_timestamp()
    should_backup = backup and destination.exists()
    dry_action = "install"
    run_action = "Installed"

    if destination.exists():
        dry_action = "replace"
        run_action = "Replaced"

    dry_messages = [f"Would {dry_action} templates at: {destination}"]
    run_messages = [f"{run_action} templates at: {destination}"]

    if should_backup:
        backup_path = template_backup_path(backup_root, timestamp)
        dry_messages.insert(0, f"Would back up existing templates to: {backup_path}")
        run_messages.insert(0, f"Backed up existing templates to: {backup_path}")

    def execute() -> None:
        if should_backup:
            backup_destination(destination, backup_root, kind="templates", timestamp=timestamp)
        if destination.exists():
            remove_path(destination)
        copy_tree(source, destination)

    return PlannedAction(dry_messages, run_messages, execute)


def plan_template_uninstall(
    *,
    destination: Path,
    backup_root: Path,
    dry_run: bool,
    backup: bool,
) -> PlannedAction | None:
    """Plan removal of the shared templates directory."""
    if not destination.exists():
        return None

    timestamp = utc_timestamp()
    should_backup = backup and destination.exists()
    dry_messages = [f"Would remove templates from: {destination}"]
    run_messages = [f"Removed templates from: {destination}"]

    if should_backup:
        backup_path = template_backup_path(backup_root, timestamp)
        dry_messages.insert(0, f"Would back up existing templates to: {backup_path}")
        run_messages.insert(0, f"Backed up existing templates to: {backup_path}")

    def execute() -> None:
        if should_backup:
            backup_destination(destination, backup_root, kind="templates", timestamp=timestamp)
        remove_path(destination)

    return PlannedAction(dry_messages, run_messages, execute)


def print_messages(messages: list[str]) -> None:
    """Print a list of action messages."""
    for message in messages:
        print(message)


def print_errors(errors: list[str]) -> None:
    """Print validation or planning errors."""
    for error in errors:
        print(f"error: {error}", file=sys.stderr)


def print_install_summary(
    *,
    display_name: str,
    skills: list[str],
    target_root: Path,
    command_prefix: str,
    dry_run: bool,
) -> None:
    """Print the final install summary and invocation examples."""
    if skills:
        print(
            f"Installed {len(skills)} skills into: {target_root}"
            if not dry_run
            else f"Would install {len(skills)} skills into: {target_root}"
        )
        for skill_name in skills:
            print(f"- {skill_name}")

    if skills:
        heading = f"{display_name} slash commands that would be available:" if dry_run else f"{display_name} slash commands:"
        print(heading)
        for skill_name in skills:
            print(f"{command_prefix}{skill_name}")
    elif not skills:
        print(f"No skills selected for installation into: {target_root}")


def print_removal_summary(
    *,
    skills: list[str],
    target_root: Path,
    dry_run: bool,
) -> None:
    """Print the final uninstall summary."""
    if skills:
        print(
            f"Removed {len(skills)} skills from: {target_root}"
            if not dry_run
            else f"Would remove {len(skills)} skills from: {target_root}"
        )
        for skill_name in skills:
            print(f"- {skill_name}")
    else:
        print(f"No managed skills selected for removal from: {target_root}")


def run_installer(spec: InstallerSpec, args: argparse.Namespace) -> int:
    """Run the chosen installer end-to-end."""
    validate_repo_paths()
    valid_skill_names = available_skill_names()
    selected_skill_names = selected_skill_names_from_args(args.only, valid_skill_names)
    skill_target = spec.resolve_skill_target(args)
    support_root = spec.resolve_support_root(args)
    template_target = support_root / "templates"
    backup_root = support_root / "backups"
    planning_errors: list[str] = []

    if args.uninstall:
        planned_actions: list[PlannedAction] = []
        removed_skill_names: list[str] = []
        template_action_planned = False

        for skill_name in selected_skill_names:
            destination = skill_target / skill_name
            try:
                action = plan_skill_uninstall(
                    skill_name=skill_name,
                    destination=destination,
                    backup_root=backup_root,
                    dry_run=args.dry_run,
                    backup=args.backup,
                    force=args.force,
                )
            except InstallerError as exc:
                planning_errors.append(str(exc))
                continue

            if action is not None:
                planned_actions.append(action)
                removed_skill_names.append(skill_name)

        if args.include_templates:
            try:
                template_action = plan_template_uninstall(
                    destination=template_target,
                    backup_root=backup_root,
                    dry_run=args.dry_run,
                    backup=args.backup,
                )
            except InstallerError as exc:
                planning_errors.append(str(exc))
            else:
                if template_action is not None:
                    planned_actions.append(template_action)
                    template_action_planned = True

        if planning_errors:
            if args.dry_run:
                for action in planned_actions:
                    print_messages(action.dry_messages)
            print_errors(planning_errors)
            return 1

        if args.dry_run:
            for action in planned_actions:
                print_messages(action.dry_messages)
            if removed_skill_names:
                print_removal_summary(
                    skills=removed_skill_names,
                    target_root=skill_target,
                    dry_run=True,
                )
            elif not template_action_planned:
                print_removal_summary(
                    skills=[],
                    target_root=skill_target,
                    dry_run=True,
                )
            return 0

        if not planned_actions:
            print_removal_summary(
                skills=[],
                target_root=skill_target,
                dry_run=False,
            )
            return 0

        for action in planned_actions:
            action.executor()
            print_messages(action.run_messages)

        if removed_skill_names:
            print_removal_summary(
                skills=removed_skill_names,
                target_root=skill_target,
                dry_run=False,
            )
        elif not template_action_planned:
            print_removal_summary(
                skills=[],
                target_root=skill_target,
                dry_run=False,
            )
        return 0

    planned_actions = []
    for skill_name in selected_skill_names:
        source = SKILLS_DIR / skill_name
        destination = skill_target / skill_name
        try:
            planned_actions.append(
                plan_skill_install(
                    spec,
                    skill_name=skill_name,
                    source=source,
                    destination=destination,
                    backup_root=backup_root,
                    dry_run=args.dry_run,
                    backup=args.backup,
                    force=args.force,
                )
            )
        except InstallerError as exc:
            planning_errors.append(str(exc))

    if args.include_templates:
        try:
            planned_actions.append(
                plan_template_install(
                    source=TEMPLATES_DIR,
                    destination=template_target,
                    backup_root=backup_root,
                    dry_run=args.dry_run,
                    backup=args.backup,
                )
            )
        except InstallerError as exc:
            planning_errors.append(str(exc))

    if planning_errors:
        if args.dry_run:
            for action in planned_actions:
                print_messages(action.dry_messages)
        print_errors(planning_errors)
        return 1

    if args.dry_run:
        for action in planned_actions:
            print_messages(action.dry_messages)
        print_install_summary(
            display_name=spec.display_name,
            skills=selected_skill_names,
            target_root=skill_target,
            command_prefix=spec.command_prefix,
            dry_run=True,
        )
        return 0

    for action in planned_actions:
        action.executor()
        print_messages(action.run_messages)

    print_install_summary(
        display_name=spec.display_name,
        skills=selected_skill_names,
        target_root=skill_target,
        command_prefix=spec.command_prefix,
        dry_run=False,
    )
    return 0


def selected_skill_names_from_args(only: str | None, valid_names: list[str]) -> list[str]:
    """Shim used by run_installer to keep a short public API."""
    return selected_skill_names(only, valid_names)
