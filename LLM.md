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
- you want explicit verification evidence
- another session needs durable continuation state

Use `ceremony-budget` first when the safe route is unclear. Tiny reversible edits and
low-ambiguity micro changes may not need durable artifacts at all.

## Default durable loop

```text
mini-spec -> scope-freeze -> build-one -> verify-contract -> handoff
```

Use this as the default durable loop for a bounded vertical slice. Do not widen the
slice unless the spec is updated first. Add `test-mini` when behavior changed and a
focused deterministic test is practical. Use `handoff` only when another session or
agent actually needs continuation state.

The starter bundle is an installation convenience, not a mandate to invoke every
installed skill on every task.

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
./install.sh --claude-user --only mini-spec,scope-freeze,build-one,verify-contract,handoff
./install.sh --codex-user --only mini-spec,scope-freeze,build-one,verify-contract,handoff
python scripts/run_runnable_examples.py
python scripts/run_negative_examples.py
python scripts/verify_gate.py
```

## Agent operating rules

- Keep changes small and local.
- Update the spec before expanding scope.
- Use `test-mini` when focused deterministic tests add value.
- Use `verify-contract` as the proof gate, not a guess.
- Preserve handoff state when a fresh context must continue without re-deriving the work.
- Prefer the repo's templates and scripts over inventing new process.
- Do not change skill behavior while making documentation-only edits.

## What counts as done

- The intended files are updated.
- Validation passes, or any failure is explained with concrete output.
- Verification evidence exists for behavior changes.
- When handoff is used, it captures the current phase, next gate, context risk, and active hypothesis.
- A fresh session could resume from recorded artifacts when continuation is required.

## What not to do

- Do not expand scope without updating the spec.
- Do not claim completion without verification evidence.
- Do not delete or flatten handoff state.
- Do not rewrite the README unless asked.
- Do not add framework complexity or generated marketing copy.
- Do not use this guide to change skill behavior.
