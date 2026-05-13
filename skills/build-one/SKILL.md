---
name: build-one
description: Implement exactly one planned slice, run the relevant verification, summarize the result, and stop before starting another task.
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
6. Update task status.
7. Stop after one task.
8. Summarize changed files and result.

## Outputs

- One implemented slice
- Changed file summary
- Verification result
- Updated `TODO.md` if appropriate

## Stop conditions

- The selected task is complete and verified.
- The task needs a scope change.
- Verification fails and diagnosis is needed.

## Anti-patterns

- Continuing into the next task without approval.
- Refactoring unrelated code.
- Treating partial infrastructure as a completed slice.
