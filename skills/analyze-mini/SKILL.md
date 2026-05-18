---
name: analyze-mini
description: Check consistency across `CONTEXT.md`, `SPEC.md`, `PLAN.md`, `TODO.md`, and scope-freeze notes.
---

# Analyze Mini

## Purpose

Check consistency across `CONTEXT.md`, `SPEC.md`, `PLAN.md`, `TODO.md`, and scope-freeze notes before implementation.

## When to use

Use after planning and scope-freeze, before `build-one`, when a small project has enough artifacts that inconsistencies can create wasted implementation work.

## Inputs

- `CONTEXT.md`
- `SPEC.md`
- `PLAN.md`
- `TODO.md`
- Scope-freeze notes
- Selected task

## Workflow

1. Check that the objective aligns across artifacts.
2. Map acceptance criteria to planned tasks.
3. Confirm verification commands exist.
4. Confirm non-goals are not contradicted by tasks.
5. Check that scope-freeze boundaries fit the selected task.
6. Identify complexity additions and require justification.
7. Update `ANALYZE.md` with findings and the implementation readiness call.

## Outputs

- `ANALYZE.md`
- Consistency findings
- Acceptance-criteria-to-task map
- Verification gaps
- Scope compatibility notes
- Complexity notes

## Stop conditions

- The selected task is consistent with the artifacts.
- A contradiction or missing command blocks implementation.

## Anti-patterns

- Starting implementation while artifacts disagree.
- Adding complexity because it seems useful later.
- Ignoring scope-freeze limits when selecting the next task.
