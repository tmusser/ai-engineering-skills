# Compatibility Confidence

<!-- markdownlint-disable MD013 -->

This repo is portable by design, but compatibility is not exhaustive. The matrix
below describes documented install paths and release-validation expectations, not
official support from Anthropic, OpenAI, or any other tool vendor.

## Matrix

| Target | Install location | Invocation style | Tested status | Last verified | Confidence | Known caveats |
| --- | --- | --- | --- | --- | --- | --- |
| Claude Code user install | User Claude skills directory | `/skill-name` | Installer path and dry-run smoke checks | v0.6.0 release validation | High | Automatic skill invocation may vary by task and environment. Explicit slash invocation is the documented path. |
| Claude Code project install | Project `.claude/skills/` | `/skill-name` | Installer path and dry-run smoke checks | v0.6.0 release validation | High | Project-scoped behavior depends on the local Claude Code environment reading that project skill folder. |
| Codex user install | User `.agents/skills/` | `$skill-name` or `/skills` where available | Installer path and dry-run smoke checks | v0.6.0 release validation | High | Invocation and discovery may vary by Codex client behavior. Explicit `$skill-name` invocation is the documented path. |
| Codex project install | Project `.agents/skills/` plus project guidance | `$skill-name` or `/skills` where available | Installer path and dry-run smoke checks | v0.6.0 release validation | High | Project-scoped behavior depends on the local Codex environment reading project skills and guidance. |
| Manual folder copy | Tool-specific skill folder | Tool-specific | Documented fallback, not exhaustive tool testing | v0.6.0 release validation | Medium | Depends on the receiving agent reading local skill folders and honoring `SKILL.md` conventions. |
| Other agents | Varies by tool | Varies by tool | Best effort | TBD before v0.6.0 tag | Medium-low | Best-effort unless the agent supports similar skill-folder conventions and explicit invocation. |

## How to verify locally

Run a dry-run starter install before changing any local agent configuration.

Claude Code user dry run:

```bash
./install.sh --claude-user --only mini-spec,scope-freeze,build-one,verify-contract,handoff --dry-run
```

Codex user dry run:

```bash
./install.sh --codex-user --only mini-spec,scope-freeze,build-one,verify-contract,handoff --dry-run
```

Project-scoped examples:

```bash
./install.sh --claude-project /path/to/project --only mini-spec,scope-freeze,build-one,verify-contract,handoff --dry-run
./install.sh --codex-project /path/to/project --only mini-spec,scope-freeze,build-one,verify-contract,handoff --dry-run
```

Repo validation:

```bash
python scripts/validate_repo.py
python -m unittest discover tests
python scripts/run_runnable_examples.py
python scripts/run_negative_examples.py
npx markdownlint-cli2 "**/*.md"
bash install.sh --help
```

## What compatibility does not mean

Compatibility does not mean:

- official support from any vendor
- exhaustive testing across every agent version or client
- guaranteed automatic skill invocation
- guaranteed autonomous safety
- a replacement for local validation before install or update

Treat this repo as portable and inspectable, not magically universal.
