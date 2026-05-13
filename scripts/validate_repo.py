#!/usr/bin/env python3
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]

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
    "scripts/validate_repo.py",
]

SKILLS = [
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


def main() -> int:
    errors = []

    for rel in REQUIRED_FILES:
        if not (ROOT / rel).is_file():
            errors.append(f"missing file: {rel}")

    for skill in SKILLS:
        skill_file = ROOT / "skills" / skill / "SKILL.md"
        if not skill_file.is_file():
            errors.append(f"missing skill file: skills/{skill}/SKILL.md")
            continue
        text = skill_file.read_text(encoding="utf-8")
        for heading in REQUIRED_HEADINGS:
            if heading not in text:
                errors.append(f"skills/{skill}/SKILL.md missing heading: {heading}")

    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8") if (ROOT / "LICENSE").exists() else ""
    if "MIT License" not in license_text:
        errors.append("LICENSE does not contain MIT License")

    readme_text = (ROOT / "README.md").read_text(encoding="utf-8") if (ROOT / "README.md").exists() else ""
    if "bounded scope" not in readme_text:
        errors.append("README.md does not contain phrase: bounded scope")

    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Validation passed.")
    print(f"Checked {len(REQUIRED_FILES)} required files and {len(SKILLS)} skills.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
