#!/usr/bin/env python3
"""Install AI Engineering Skills for Claude Code."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills"
TEMPLATES_DIR = ROOT / "templates"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install AI Engineering Skills into Claude Code skill folders."
    )
    parser.add_argument(
        "--target",
        choices=["user", "project"],
        required=True,
        help="Install to ~/.claude/skills/ or to <project>/.claude/skills/.",
    )
    parser.add_argument(
        "--project-path",
        type=Path,
        help="Target project path. Required when --target project is used.",
    )
    parser.add_argument(
        "--include-templates",
        action="store_true",
        help="Also copy templates into a Claude-friendly support directory.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be installed without creating or replacing files.",
    )
    return parser.parse_args()


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def validate_repo_paths() -> None:
    if not SKILLS_DIR.is_dir():
        fail(f"skills directory not found: {SKILLS_DIR}")

    if not TEMPLATES_DIR.is_dir():
        fail(f"templates directory not found: {TEMPLATES_DIR}")


def skill_directories() -> list[Path]:
    skills = sorted(path for path in SKILLS_DIR.iterdir() if path.is_dir())

    if not skills:
        fail(f"no skill directories found under: {SKILLS_DIR}")

    for skill_dir in skills:
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.is_file():
            fail(f"missing SKILL.md in: {skill_dir}")

    return skills


def resolve_skill_target(args: argparse.Namespace) -> Path:
    if args.target == "user":
        return Path.home() / ".claude" / "skills"

    if args.project_path is None:
        fail("--project-path is required when --target project is used")

    project_path = args.project_path.expanduser().resolve()

    if not project_path.exists():
        fail(f"project path does not exist: {project_path}")

    if not project_path.is_dir():
        fail(f"project path is not a directory: {project_path}")

    return project_path / ".claude" / "skills"


def resolve_template_target(args: argparse.Namespace) -> Path:
    if args.target == "user":
        return Path.home() / ".claude" / "ai-engineering-skills" / "templates"

    if args.project_path is None:
        fail("--project-path is required when --target project is used")

    project_path = args.project_path.expanduser().resolve()
    return project_path / "docs" / "ai-engineering-skills" / "templates"


def copy_skill(skill_dir: Path, target_root: Path, dry_run: bool) -> str:
    destination = target_root / skill_dir.name

    if dry_run:
        if destination.exists():
            print(f"Would replace existing skill: {destination}")
        else:
            print(f"Would install skill: {destination}")
        return skill_dir.name

    if destination.exists():
        print(f"Replacing existing skill: {destination}")

    shutil.copytree(skill_dir, destination, dirs_exist_ok=True)
    return skill_dir.name


def copy_skills(skills: list[Path], target_root: Path, dry_run: bool) -> list[str]:
    if not dry_run:
        target_root.mkdir(parents=True, exist_ok=True)

    installed: list[str] = []

    for skill_dir in skills:
        installed.append(copy_skill(skill_dir, target_root, dry_run))

    return installed


def copy_templates(target_root: Path, dry_run: bool) -> None:
    if dry_run:
        if target_root.exists():
            print(f"Would replace existing templates: {target_root}")
        return

    if target_root.exists():
        print(f"Replacing existing templates: {target_root}")

    shutil.copytree(TEMPLATES_DIR, target_root, dirs_exist_ok=True)


def print_summary(skill_target: Path, installed: list[str], dry_run: bool) -> None:
    action = "Would install" if dry_run else "Installed"
    print(f"{action} {len(installed)} skills into: {skill_target}")

    for skill_name in installed:
        print(f"- {skill_name}")

    heading = "Claude Code slash commands that would be available:" if dry_run else "Claude Code slash commands:"
    print(heading)

    for skill_name in installed:
        print(f"/{skill_name}")


def main() -> int:
    args = parse_args()

    validate_repo_paths()

    skills = skill_directories()
    skill_target = resolve_skill_target(args)
    installed = copy_skills(skills, skill_target, args.dry_run)

    print_summary(skill_target, installed, args.dry_run)

    if args.include_templates:
        template_target = resolve_template_target(args)
        copy_templates(template_target, args.dry_run)
        if args.dry_run:
            print(f"Would install templates into: {template_target}")
        else:
            print(f"Installed templates into: {template_target}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
