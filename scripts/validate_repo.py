#!/usr/bin/env python3
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


def read_text(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def parse_frontmatter(lines: list[str]) -> tuple[dict[str, str], list[str]]:
    errors: list[str] = []

    if not lines or lines[0] != "---":
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
        if not key or not value:
            errors.append(f"frontmatter line {line_number} must include key and value")
            continue
        metadata[key] = value

    return metadata, errors


def main() -> int:
    errors: list[str] = []

    for rel in REQUIRED_FILES:
        if not (ROOT / rel).is_file():
            errors.append(f"missing file: {rel}")

    if not (ROOT / WORKFLOW_FILE).is_file():
        errors.append(f"missing workflow file: {WORKFLOW_FILE}")

    for skill in REQUIRED_SKILLS:
        skill_dir = ROOT / "skills" / skill
        skill_file = skill_dir / "SKILL.md"

        if not skill_dir.is_dir():
            errors.append(f"missing skill directory: skills/{skill}")
            continue

        if not skill_file.is_file():
            errors.append(f"missing skill file: skills/{skill}/SKILL.md")
            continue

        text = skill_file.read_text(encoding="utf-8")
        lines = text.splitlines()
        metadata, frontmatter_errors = parse_frontmatter(lines)

        for error in frontmatter_errors:
            errors.append(f"skills/{skill}/SKILL.md {error}")

        if metadata.get("name") != skill:
            errors.append(f"skills/{skill}/SKILL.md frontmatter name must be: {skill}")

        if not metadata.get("description"):
            errors.append(f"skills/{skill}/SKILL.md frontmatter missing description")

        for heading in REQUIRED_HEADINGS:
            if heading not in lines:
                errors.append(f"skills/{skill}/SKILL.md missing heading: {heading}")

    if (ROOT / "LICENSE").is_file() and "MIT License" not in read_text("LICENSE"):
        errors.append("LICENSE does not contain MIT License")

    if (ROOT / "README.md").is_file() and "bounded scope" not in read_text("README.md"):
        errors.append("README.md does not contain phrase: bounded scope")

    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Validation passed.")
    print(f"Checked {len(REQUIRED_FILES)} required files and {len(REQUIRED_SKILLS)} skills.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
