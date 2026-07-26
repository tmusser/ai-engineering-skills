---
name: build-one
description: Implement exactly one planned slice after scope is frozen, without exceeding the spec ceiling.
---

# Build One

## Purpose

Implement exactly one planned slice without expanding the behavioral contract.

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
4. Confirm the spec ceiling: each intended behavior change must satisfy an acceptance criterion or be necessary support for one. Explicit non-goals remain out of scope.
5. If the implementation needs behavior outside that ceiling, stop and renegotiate or update the spec before making that expansion.
6. Make the minimum useful change.
7. Run relevant verification.
8. Update `VERIFY.md` or `HANDOFF.md` with a compact build note:
   - Selected slice
   - Files touched
   - Why each file was touched
   - Compatibility seams preserved
   - Spec ceiling respected: yes/no
   - Unexpected behavior added: none | describe
   - Tests changed: yes/no
   - Verification run
   - Stop reason
9. Update task status.
10. Stop after one task.
11. Summarize changed files and result.

## Outputs

- One implemented slice
- Changed file summary
- Verification result
- Build note
- Updated `TODO.md` if appropriate

## Stop conditions

- The selected task is complete and verified.
- The task needs a scope or spec change.
- Verification fails and diagnosis is needed.
- A useful adjacent improvement is discovered but is not required by the current acceptance criteria.

## Anti-patterns

- Continuing into the next task without approval.
- Refactoring unrelated code.
- Adding "helpful" behavior beyond the acceptance criteria because it is nearby or easy.
- Treating partial infrastructure as a completed slice.
