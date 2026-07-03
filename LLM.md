# LLM.md

## What this repo is

This repo is a plain-file skill pack for Claude Code, Codex CLI, and other coding agents.
It combines self-contained skills, reusable templates, install scripts, docs, examples,
and tests so agent work can move from clarified scope to verified change to durable handoff.

It is documentation and workflow infrastructure, not an application runtime.

## When to use it

Use this repo when:

- the task is too consequential for ad hoc prompting
- the work should stay inside a bounded slice
- you need durable context between sessions
- you want verification evidence and a handoff packet at the end

## Canonical workflow loop

```text
mini-spec -> scope-freeze -> build-one -> test-mini -> verify-contract -> handoff
```

Use this as the default loop for vertical slices. Do not widen the slice unless the
spec is updated first.

## Important files and directories

- `README.md` - project overview and entry point
- `AGENTS.md` - repo-specific agent instructions
- `skills/` - self-contained skill folders with `SKILL.md`
- `templates/` - durable artifacts such as `SPEC.md`, `PLAN.md`, `VERIFY.md`, and `HANDOFF.md`
- `scripts/` - install, validation, and example runner scripts
- `docs/` - bundles, recipes, installation notes, and governance docs
- `examples/` - worked examples and failure-mode comparisons
- `demo/` - demo script, tape, and sample data
- `tests/` - validator and installer tests
- `LIMITATIONS.md` - known limits and failure modes
- `ACKNOWLEDGMENTS.md` - acknowledgments and attribution

## Common repo commands

```bash
python scripts/validate_repo.py
npx markdownlint-cli2 "**/*.md"
git diff --check
./install.sh --claude-user --only mini-spec,scope-freeze,build-one,test-mini,verify-contract,handoff
./install.sh --codex-user --only mini-spec,scope-freeze,build-one,test-mini,verify-contract,handoff
python scripts/run_runnable_examples.py
python scripts/run_negative_examples.py
python scripts/verify_gate.py
```

## Agent operating rules

- Keep changes small and local.
- Update the spec before expanding scope.
- Use `test-mini` and `verify-contract` as the proof gate, not a guess.
- Preserve handoff state so a fresh context can continue without re-deriving the work.
- Prefer the repo's templates and scripts over inventing new process.
- Do not change skill behavior while making documentation-only edits.

## What counts as done

- The intended files are updated.
- Validation passes, or any failure is explained with concrete output.
- Verification evidence exists for behavior changes.
- Handoff state captures the current phase, next gate, context risk, and active hypothesis.
- A fresh session could resume from the recorded artifacts.

## What not to do

- Do not expand scope without updating the spec.
- Do not claim completion without verification evidence.
- Do not delete or flatten handoff state.
- Do not rewrite the README unless asked.
- Do not add framework complexity or generated marketing copy.
- Do not use this guide to change skill behavior.
