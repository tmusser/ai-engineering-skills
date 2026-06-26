---
name: build-one
description: Implement exactly one planned slice after scope is frozen.
---

# Build One

## Purpose

Implement exactly one planned slice.

## When to use

Use after a task is selected and scope is frozen.

## Inputs

- `SPEC.md`
- `PLAN.md`
- `TODO.md`
- Scope boundary
- Current repo status

## Workflow

1. Read `SPEC.md`, `PLAN.md`, and `TODO.md`.
2. Select one task.
3. Confirm the scope boundary.
4. Make the minimum useful change.
5. Run relevant verification.
6. Update `VERIFY.md` or `HANDOFF.md` with a compact build note:
   - Selected slice
   - Files touched
   - Why each file was touched
   - Compatibility seams preserved
   - Tests changed: yes/no
   - Verification run
   - Stop reason
7. Update task status.
8. Stop after one task.
9. Summarize changed files and result.

## Outputs

- One implemented slice
- Changed file summary
- Verification result
- Build note
- Updated `TODO.md` if appropriate

## Stop conditions

- The selected task is complete and verified.
- The task needs a scope change.
- Verification fails and diagnosis is needed.

## Anti-patterns

- Continuing into the next task without approval.
- Refactoring unrelated code.
- Treating partial infrastructure as a completed slice.
