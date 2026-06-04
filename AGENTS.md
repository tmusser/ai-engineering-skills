# Agent Instructions

This repo is mostly Markdown process artifacts plus small standard-library Python scripts.

Preserve concise, actionable wording.

Do not add unnecessary framework complexity.

Do not copy from external skill repos.

Keep each skill self-contained.

When editing a skill, update related templates if needed.

Run validation after changes:

```bash
python -m py_compile scripts/validate_repo.py
python -m py_compile scripts/install_claude_code.py
python scripts/validate_repo.py
```

Prefer small diffs.

Preserve the MIT license and acknowledgments.

Do not add generated marketing fluff.

When editing handoff behavior, preserve `Workflow state`: active modes, current phase, current loop, next gate, context risk, and active hypothesis. Do not expand handoff into a transcript summary.

## Quality standards

Every skill must include YAML frontmatter:

- `name`
- `description`

Every skill must include:

- Purpose
- When to use
- Inputs
- Workflow
- Outputs
- Stop conditions
- Anti-patterns

Every template must be short and directly usable.

Every example must show a concrete use case.

Every install path must remain portable across tools.

Claude Code support is first-class.

Codex support is maintained.

Manual install must remain possible because skills are plain folders with `SKILL.md` files.
