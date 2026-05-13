# Codex Installation

Codex is supported, but this repository is not Codex-only.

Each skill is a plain folder with a `SKILL.md` file. Use the skills by copying or referencing them in the appropriate Codex skill directory for your environment.

For repo-scoped usage, a common pattern is:

```bash
mkdir -p .agents/skills docs/ai-workflow
cp -R /path/to/ai-engineering-skills/skills/* .agents/skills/
cp -R /path/to/ai-engineering-skills/templates/* docs/ai-workflow/
```

Then ask Codex:

```text
Use $grill-with-docs-lite, then $mini-spec and $thin-plan for this project. Stop before implementation.
```

Use `docs/ai-workflow/` or the project root for durable artifacts such as `SPEC.md`, `PLAN.md`, `VERIFY.md`, and `HANDOFF.md`.

If your Codex environment uses a different skill location, copy the folders from `skills/` there instead.
