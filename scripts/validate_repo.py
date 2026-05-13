#!/usr/bin/env python3
"""Validate the repository structure for AI Engineering Skills."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_FILE = ".github/workflows/validate.yml"

REQUIRED_FILES = [
    "README.md",
    "LICENSE",
    "ACKNOWLEDGMENTS.md",
    "AGENTS.md",
    "templates/CONTEXT.md",
    "templates/SPEC.md",
    "templates/PLAN.md",
    "templates/TODO.md",
    "templates/BUGS.md",
    "templates/DECISIONS.md",
    "templates/VERIFY.md",
    "templates/SHIP.md",
    "templates/HANDOFF.md",
    "examples/small-dashboard-poc.md",
    "examples/agent-worker-poc.md",
    "examples/ml-model-poc.md",
    WORKFLOW_FILE,
    "scripts/validate_repo.py",
]

REQUIRED_SKILLS = [
    "grill-with-docs-lite",
    "mini-spec",
    "thin-plan",
    "scope-freeze",
    "build-one",
    "test-mini",
    "diagnose-loop",
    "bug-capture",
    "verify-contract",
    "ship-mini",
    "handoff",
]

REQUIRED_HEADINGS = [
    "## Purpose",
    "## When to use",
    "## Inputs",
    "## Workflow",
    "## Outputs",
    "## Stop conditions",
    "## Anti-patterns",
]


def repo_path(relative_path: str) -> Path:
    """Return an absolute path inside the repository."""
    return ROOT / relative_path


def read_text(relative_path: str) -> str:
    """Read a UTF-8 text file from the repository."""
    return repo_path(relative_path).read_text(encoding="utf-8")


def check_required_files(errors: list[str]) -> None:
    """Check that all required top-level artifacts exist."""
    for relative_path in REQUIRED_FILES:
        if not repo_path(relative_path).is_file():
            errors.append(f"missing file: {relative_path}")


def parse_frontmatter(lines: list[str]) -> tuple[dict[str, str], list[str]]:
    """Parse simple YAML frontmatter from a SKILL.md file."""
    errors: list[str] = []

    if not lines:
        return {}, ["file is empty"]

    if lines[0] != "---":
        return {}, ["frontmatter must start with --- on line 1"]

    try:
        end_index = lines[1:].index("---") + 1
    except ValueError:
        return {}, ["frontmatter must end with --- on its own line"]

    metadata: dict[str, str] = {}

    for line_number, line in enumerate(lines[1:end_index], start=2):
        if not line.strip():
            continue

        if ":" not in line:
            errors.append(f"frontmatter line {line_number} is not key: value")
            continue

        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()

        if not key:
            errors.append(f"frontmatter line {line_number} has an empty key")
            continue

        if not value:
            errors.append(f"frontmatter line {line_number} has an empty value")
            continue

        metadata[key] = value

    return metadata, errors


def check_skill(skill_name: str, errors: list[str]) -> None:
    """Check one skill directory and SKILL.md contract."""
    skill_dir = repo_path(f"skills/{skill_name}")
    skill_file = skill_dir / "SKILL.md"

    if not skill_dir.is_dir():
        errors.append(f"missing skill directory: skills/{skill_name}")
        return

    if not skill_file.is_file():
        errors.append(f"missing skill file: skills/{skill_name}/SKILL.md")
        return

    lines = skill_file.read_text(encoding="utf-8").splitlines()
    metadata, frontmatter_errors = parse_frontmatter(lines)

    for error in frontmatter_errors:
        errors.append(f"skills/{skill_name}/SKILL.md {error}")

    if metadata.get("name") != skill_name:
        errors.append(
            f"skills/{skill_name}/SKILL.md frontmatter name must be: {skill_name}"
        )

    if "description" not in metadata:
        errors.append(f"skills/{skill_name}/SKILL.md frontmatter missing description")

    for heading in REQUIRED_HEADINGS:
        if heading not in lines:
            errors.append(f"skills/{skill_name}/SKILL.md missing heading: {heading}")


def check_skills(errors: list[str]) -> None:
    """Check all required skills."""
    for skill_name in REQUIRED_SKILLS:
        check_skill(skill_name, errors)


def check_license(errors: list[str]) -> None:
    """Check that the license declares MIT."""
    license_path = repo_path("LICENSE")
    if license_path.is_file() and "MIT License" not in read_text("LICENSE"):
        errors.append("LICENSE does not contain MIT License")


def check_readme(errors: list[str]) -> None:
    """Check that the README contains the core positioning phrase."""
    readme_path = repo_path("README.md")
    if readme_path.is_file() and "bounded scope" not in read_text("README.md"):
        errors.append("README.md does not contain phrase: bounded scope")


def check_workflow(errors: list[str]) -> None:
    """Check that the GitHub Actions workflow exists."""
    if not repo_path(WORKFLOW_FILE).is_file():
        errors.append(f"missing workflow file: {WORKFLOW_FILE}")


def main() -> int:
    """Run all validation checks."""
    errors: list[str] = []

    check_required_files(errors)
    check_skills(errors)
    check_readme(errors)
    check_license(errors)
    check_workflow(errors)

    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Validation passed.")
    print(f"Checked {len(REQUIRED_FILES)} required files.")
    print(f"Checked {len(REQUIRED_SKILLS)} required skills.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
