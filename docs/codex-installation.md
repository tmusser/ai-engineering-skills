# Codex Installation

Codex is a first-class target for this repo.

Each skill is a plain folder with a `SKILL.md` file. Codex can use these skills from a user-level skill directory or from a repo-scoped skill directory.

## Install Modes

### User Install

Install skills for use across Codex projects:

```bash
python scripts/install_codex.py --target user
```

This installs the selected skill folders into:

```text
~/.agents/skills/
```

### Project Install

Install skills into a specific project:

```bash
python scripts/install_codex.py --target project --project-path /path/to/project
```

This installs the selected skill folders into:

```text
<project>/.agents/skills/
```

Use project install when you want the workflow versioned with a repo and shared by a team.

Managed, unmodified skill folders update normally. Unmanaged or locally modified skill folders are refused by default and require `--force`. Use `--backup` before replacing or removing existing installs, and start with `--dry-run` when you want to inspect the plan first.

## Templates

Templates are not installed by default.

To copy templates during install:

```bash
python scripts/install_codex.py --target user --include-templates
python scripts/install_codex.py --target project --project-path /path/to/project --include-templates
```

Template destinations:

- User install: `~/.agents/ai-engineering-skills/templates/`
- Project install: `<project>/docs/ai-engineering-skills/templates/`

## Safety behavior

The installer writes `AI_ENGINEERING_SKILLS_VERSION.json` into each installed skill folder.

- `--dry-run` prints what would happen and makes no changes.
- `--only mini-spec,scope-freeze` installs or uninstalls just those skills.
- `--backup` copies replaced or removed folders to a timestamped backup root before mutation.
- `--force` is required to overwrite unmanaged or locally modified installs.
- `--uninstall` removes selected skills instead of installing them.
- `--include-templates` copies templates with the same backup behavior.

When in doubt, run `--dry-run` first.

## Invocation

Codex skills should be invoked with `$skill-name` or selected through `/skills`.

Examples:

```text
$mini-spec
$thin-plan
$scope-freeze
$build-one
$verify-contract
$lean-mode
$context-check
$handoff
```

Use `/skills` when you want to browse or select installed skills interactively.

Codex can also invoke skills implicitly when the task matches the skill description.

Do not assume Claude Code slash commands such as `/mini-spec` work in Codex. Codex uses its own skill invocation conventions.

## Project Guidance

A project `AGENTS.md` pairs well with these skills.

Use it to state local rules, validation commands, ownership boundaries, and any tool-specific guidance the agent should read before acting.

Then ask Codex with explicit skill names:

```text
Use $grill-with-docs-lite, then $mini-spec and $thin-plan for this project. Stop before implementation.
```
