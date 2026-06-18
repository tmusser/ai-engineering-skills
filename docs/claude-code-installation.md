# Claude Code Installation

Claude Code is the primary installation path for this repository.

This is not an official Anthropic plugin.

It is a filesystem-based skill pack made of plain folders that contain `SKILL.md` files.

Claude Code can use filesystem-based skills from these locations:

- `~/.claude/skills/` for personal skills available across projects
- `<project>/.claude/skills/` for project skills shared with a repo

## Personal install

Use a personal install when you want these skills available across all Claude Code projects.

Run this command from the root of this repository:

```bash
python scripts/install_claude_code.py --target user
```

This copies each folder under `skills/` into:

```text
~/.claude/skills/
```

Existing skill folders with the same names are replaced after the script prints what will be replaced.

## Project install

Use a project install when you want the skills versioned with a specific project.

Run this command from the root of this repository:

```bash
python scripts/install_claude_code.py --target project --project-path /path/to/project
```

This copies each folder under `skills/` into:

```text
<target-project>/.claude/skills/
```

Commit the copied skills in the target project when you want the team to share the same workflow.

## Include templates

By default, the installer copies only skills.

To also copy templates, pass:

```bash
--include-templates
```

For a personal install, templates are copied into:

```text
~/.claude/ai-engineering-skills/templates/
```

For a project install, templates are copied into:

```text
<target-project>/docs/ai-engineering-skills/templates/
```

## Safety behavior

The installer writes `AI_ENGINEERING_SKILLS_VERSION.json` into each installed skill folder.

- `--dry-run` prints what would happen and makes no changes.
- `--only mini-spec,scope-freeze` installs or uninstalls just those skills.
- `--backup` copies replaced or removed folders to a timestamped backup root before mutation.
- `--force` is required to overwrite unmanaged or locally modified installs.
- `--uninstall` removes selected skills instead of installing them.
- `--include-templates` copies templates with the same backup behavior.

When in doubt, run `--dry-run` first.

## Usage examples

After installation, invoke skills directly:

```text
/mini-spec
/thin-plan
/scope-freeze
/build-one
/test-mini
/diagnose-loop
/lean-mode
/context-check
/handoff
```

Claude may also invoke skills automatically when their descriptions match the task.

Use workflow artifacts such as `SPEC.md`, `PLAN.md`, `VERIFY.md`, and `HANDOFF.md` to keep project context durable.

## Invocation

The skill folder name becomes the Claude Code slash command.

For example, this folder:

```text
skills/mini-spec/
```

is invoked as:

```text
/mini-spec
```

Available slash commands:

```text
/grill-with-docs-lite
/mini-spec
/thin-plan
/scope-freeze
/build-one
/test-mini
/diagnose-loop
/bug-capture
/verify-contract
/ship-mini
/lean-mode
/context-check
/handoff
```

Claude may also invoke an installed skill automatically when the skill description matches the task.
