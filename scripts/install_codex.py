#!/usr/bin/env python3
"""Install AI Engineering Skills for Codex."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills"
TEMPLATES_DIR = ROOT / "templates"

EXAMPLE_COMMANDS = [
    "mini-spec",
    "thin-plan",
    "scope-freeze",
    "build-one",
    "verify-contract",
    "lean-mode",
    "handoff",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install AI Engineering Skills into Codex skill folders."
    )
    parser.add_argument(
        "--target",
        choices=["user", "project"],
        required=True,
        help="Install to ~/.agents/skills/ or to <project>/.agents/skills/.",
    )
    parser.add_argument(
        "--project-path",
        type=Path,
        help="Target project path. Required when --target project is used.",
    )
    parser.add_argument(
        "--include-templates",
        action="store_true",
        help="Also copy templates into a Codex-friendly support directory.",
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


def resolve_project_path(args: argparse.Namespace) -> Path:
    if args.project_path is None:
        fail("--project-path is required when --target project is used")

    project_path = args.project_path.expanduser().resolve()

    if not project_path.exists():
        fail(f"project path does not exist: {project_path}")

    if not project_path.is_dir():
        fail(f"project path is not a directory: {project_path}")

    return project_path


def resolve_skill_target(args: argparse.Namespace) -> Path:
    if args.target == "user":
        return Path.home() / ".agents" / "skills"

    project_path = resolve_project_path(args)
    return project_path / ".agents" / "skills"


def resolve_template_target(args: argparse.Namespace) -> Path:
    if args.target == "user":
        return Path.home() / ".agents" / "ai-engineering-skills" / "templates"

    project_path = resolve_project_path(args)
    return project_path / "docs" / "ai-engineering-skills" / "templates"


def copy_skill(skill_dir: Path, target_root: Path) -> str:
    destination = target_root / skill_dir.name

    if destination.exists():
        print(f"Replacing existing skill: {destination}")

    shutil.copytree(skill_dir, destination, dirs_exist_ok=True)
    return skill_dir.name


def copy_skills(skills: list[Path], target_root: Path) -> list[str]:
    target_root.mkdir(parents=True, exist_ok=True)

    installed: list[str] = []

    for skill_dir in skills:
        installed.append(copy_skill(skill_dir, target_root))

    return installed


def copy_templates(target_root: Path) -> None:
    if target_root.exists():
        print(f"Replacing existing templates: {target_root}")

    shutil.copytree(TEMPLATES_DIR, target_root, dirs_exist_ok=True)


def print_summary(skill_target: Path, installed: list[str]) -> None:
    print(f"Installed {len(installed)} skills into: {skill_target}")

    for skill_name in installed:
        print(f"- {skill_name}")

    print("Codex invocation examples:")

    for skill_name in EXAMPLE_COMMANDS:
        if skill_name in installed:
            print(f"${skill_name}")

    print("Use /skills to browse or select installed skills.")


def main() -> int:
    args = parse_args()

    validate_repo_paths()

    skills = skill_directories()
    skill_target = resolve_skill_target(args)
    installed = copy_skills(skills, skill_target)

    print_summary(skill_target, installed)

    if args.include_templates:
        template_target = resolve_template_target(args)
        copy_templates(template_target)
        print(f"Installed templates into: {template_target}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
