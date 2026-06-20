#!/usr/bin/env python3
"""Validate the repository structure for AI Engineering Skills."""

from __future__ import annotations

import py_compile
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_FILE = ".github/workflows/validate.yml"

REQUIRED_FILES = [
    "README.md",
    "LIMITATIONS.md",
    "LICENSE",
    "ACKNOWLEDGMENTS.md",
    "AGENTS.md",
    "templates/CONTEXT.md",
    "templates/CONSTITUTION.md",
    "templates/SPEC.md",
    "templates/CHECKLIST.md",
    "templates/PLAN.md",
    "templates/TODO.md",
    "templates/ANALYZE.md",
    "templates/BUGS.md",
    "templates/DECISIONS.md",
    "templates/VERIFY.md",
    "templates/SHIP.md",
    "templates/HANDOFF.md",
    "templates/STAKEHOLDER_ASKS.md",
    "examples/small-dashboard-poc.md",
    "examples/agent-worker-poc.md",
    "examples/ml-model-poc.md",
    "examples/cross-functional-infrastructure-coordination.md",
    "demo/README.md",
    "demo/sample-data/customers.csv",
    "demo/demo-script.md",
    "demo/demo.tape",
    "assets/demo.gif",
    WORKFLOW_FILE,
    "install.sh",
    "scripts/render_demo.sh",
    "scripts/run_runnable_examples.py",
    "scripts/run_negative_examples.py",
    "scripts/validate_repo.py",
    "tests/test_installers.py",
    "tests/snapshots/install_sh_help.txt",
    "tests/snapshots/install_claude_user_dry_run_only_mini_spec.txt",
    "tests/snapshots/install_codex_user_dry_run_only_mini_spec.txt",
    ".markdownlint-cli2.yaml",
]

REQUIRED_DOCS = [
    "docs/claude-code-installation.md",
    "docs/codex-installation.md",
    "docs/bundles.md",
    "docs/recipes.md",
]

REQUIRED_SCRIPTS = [
    "scripts/install_common.py",
    "scripts/install_claude_code.py",
    "scripts/install_codex.py",
    "scripts/run_runnable_examples.py",
    "scripts/run_negative_examples.py",
]

REQUIRED_SKILLS = [
    "grill-with-docs-lite",
    "constitution-lite",
    "lean-mode",
    "context-check",
    "mini-spec",
    "checklist-mini",
    "thin-plan",
    "scope-freeze",
    "analyze-mini",
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

REQUIRED_README_PHRASES = [
    "bounded scope",
    "Claude Code",
    "Codex",
    "Slash-style usage",
    "Why this exists",
    "anti-patterns",
    "Demo",
    "Limitations",
    "demo/demo.tape",
    "assets/demo.gif",
    "Workflow recipes",
    "Optional bundles",
    "Cross-functional infrastructure coordination",
    "Skill map",
    "The failure mode this avoids",
    "Ceremony ladder",
    "Analytical deliverables",
    "lean-mode",
    "context-check",
    "communication density",
    "passive guardrail",
    "AI_ENGINEERING_SKILLS_VERSION.json",
    "--backup",
    "--force",
    "--uninstall",
    "--only",
    "--include-templates",
    "```mermaid",
    "--codex-user",
    "scripts/install_codex.py",
]


def repo_path(relative_path: str) -> Path:
    """Return an absolute path inside the repository."""
    return ROOT / relative_path


def read_text(relative_path: str) -> str:
    """Read a UTF-8 text file from the repository."""
    return repo_path(relative_path).read_text(encoding="utf-8")


def check_file_exists(relative_path: str, errors: list[str]) -> None:
    """Check that a required file exists."""
    if not repo_path(relative_path).is_file():
        errors.append(f"missing file: {relative_path}")


def check_required_files(errors: list[str]) -> None:
    """Check required repository files, docs, scripts, and workflow."""
    for relative_path in REQUIRED_FILES:
        check_file_exists(relative_path, errors)

    for relative_path in REQUIRED_DOCS:
        check_file_exists(relative_path, errors)

    for relative_path in REQUIRED_SCRIPTS:
        check_file_exists(relative_path, errors)

    check_file_exists(WORKFLOW_FILE, errors)


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
    """Check one skill directory and its SKILL.md contract."""
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

    if skill_name == "lean-mode":
        skill_text = "\n".join(lines)
        if "Compress prose, not meaning" not in skill_text:
            errors.append("skills/lean-mode/SKILL.md missing phrase: Compress prose, not meaning")
        if "Always preserve" not in skill_text:
            errors.append("skills/lean-mode/SKILL.md missing phrase: Always preserve")

    if skill_name == "context-check":
        skill_text = "\n".join(lines)
        if "Detect context drift" not in skill_text:
            errors.append("skills/context-check/SKILL.md missing phrase: Detect context drift")
        if "Keep FREEZE NOW limited" not in skill_text:
            errors.append("skills/context-check/SKILL.md missing phrase: Keep FREEZE NOW limited")


def check_skills(errors: list[str]) -> None:
    """Check all required skill directories."""
    for skill_name in REQUIRED_SKILLS:
        check_skill(skill_name, errors)


def check_readme(errors: list[str]) -> None:
    """Check README positioning requirements."""
    readme_path = repo_path("README.md")

    if not readme_path.is_file():
        return

    readme = read_text("README.md")

    for phrase in REQUIRED_README_PHRASES:
        if phrase not in readme:
            errors.append(f"README.md does not contain phrase: {phrase}")


def check_license(errors: list[str]) -> None:
    """Check that the license declares MIT."""
    license_path = repo_path("LICENSE")

    if license_path.is_file() and "MIT License" not in read_text("LICENSE"):
        errors.append("LICENSE does not contain MIT License")


def check_docs(errors: list[str]) -> None:
    """Check required documentation signals."""
    docs_to_check = [
        "docs/claude-code-installation.md",
        "docs/codex-installation.md",
    ]

    for relative_path in docs_to_check:
        path = repo_path(relative_path)
        if path.is_file() and "/mini-spec" not in read_text(relative_path):
            errors.append(f"{relative_path} does not mention /mini-spec")

    claude_path = repo_path("docs/claude-code-installation.md")
    if claude_path.is_file() and "/lean-mode" not in read_text("docs/claude-code-installation.md"):
        errors.append("docs/claude-code-installation.md does not mention /lean-mode")
    if claude_path.is_file() and "/context-check" not in read_text("docs/claude-code-installation.md"):
        errors.append("docs/claude-code-installation.md does not mention /context-check")
    if claude_path.is_file() and "Safety behavior" not in read_text("docs/claude-code-installation.md"):
        errors.append("docs/claude-code-installation.md does not mention Safety behavior")

    codex_path = repo_path("docs/codex-installation.md")
    if codex_path.is_file() and "$mini-spec" not in read_text("docs/codex-installation.md"):
        errors.append("docs/codex-installation.md does not mention $mini-spec")
    if codex_path.is_file() and "$lean-mode" not in read_text("docs/codex-installation.md"):
        errors.append("docs/codex-installation.md does not mention $lean-mode")
    if codex_path.is_file() and "$context-check" not in read_text("docs/codex-installation.md"):
        errors.append("docs/codex-installation.md does not mention $context-check")
    if codex_path.is_file() and "Safety behavior" not in read_text("docs/codex-installation.md"):
        errors.append("docs/codex-installation.md does not mention Safety behavior")

    recipes_path = repo_path("docs/recipes.md")
    if recipes_path.is_file():
        recipes = read_text("docs/recipes.md")
        if "context-check" not in recipes:
            errors.append("docs/recipes.md does not mention context-check")
        if "Cross-functional infrastructure coordination" not in recipes:
            errors.append(
                "docs/recipes.md does not mention Cross-functional infrastructure coordination"
            )
        if "Analytical deliverable" not in recipes:
            errors.append("docs/recipes.md does not mention Analytical deliverable")
        if "Use test-mini for correctness checks" not in recipes:
            errors.append("docs/recipes.md does not mention Use test-mini for correctness checks")
        if "Level 0 — Patch" not in recipes:
            errors.append("docs/recipes.md does not mention Level 0 — Patch")
        if "Fresh-context development loop" not in recipes:
            errors.append("docs/recipes.md does not mention Fresh-context development loop")
        if "Spike / scratchpad" not in recipes:
            errors.append("docs/recipes.md does not mention Spike / scratchpad")
        if "```mermaid" not in recipes:
            errors.append("docs/recipes.md does not contain a Mermaid code block")


def check_python_compiles(relative_path: str, errors: list[str]) -> None:
    """Check that a Python file compiles."""
    path = repo_path(relative_path)

    if not path.is_file():
        return

    try:
        py_compile.compile(str(path), doraise=True)
    except py_compile.PyCompileError as exc:
        errors.append(f"{relative_path} does not compile: {exc.msg}")


def check_python_scripts(errors: list[str]) -> None:
    """Check Python script syntax."""
    check_python_compiles("scripts/install_common.py", errors)
    check_python_compiles("scripts/validate_repo.py", errors)
    check_python_compiles("scripts/install_claude_code.py", errors)
    check_python_compiles("scripts/install_codex.py", errors)
    check_python_compiles("scripts/run_runnable_examples.py", errors)
    check_python_compiles("scripts/run_negative_examples.py", errors)
    check_python_compiles("tests/test_installers.py", errors)


def check_shell_scripts(errors: list[str]) -> None:
    """Check shell script syntax."""
    install_sh = repo_path("install.sh")

    if not install_sh.is_file():
        return

    try:
        subprocess.run(["sh", "-n", str(install_sh)], cwd=ROOT, check=True, capture_output=True, text=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        stderr = ""
        if isinstance(exc, subprocess.CalledProcessError):
            stderr = exc.stderr.strip()
        errors.append(f"install.sh does not pass sh -n{': ' + stderr if stderr else ''}")


def main() -> int:
    """Run all validation checks."""
    errors: list[str] = []

    check_required_files(errors)
    check_skills(errors)
    check_readme(errors)
    check_docs(errors)
    check_license(errors)
    check_python_scripts(errors)
    check_shell_scripts(errors)

    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Validation passed.")
    print(f"Checked {len(REQUIRED_FILES)} required files.")
    print(f"Checked {len(REQUIRED_DOCS)} required docs.")
    print(f"Checked {len(REQUIRED_SCRIPTS)} required scripts.")
    print(f"Checked {len(REQUIRED_SKILLS)} required skills.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
