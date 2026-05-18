---
name: thin-plan
description: Convert a mini-spec into 3-7 vertical implementation slices.
---

# Thin Plan

## Purpose

Convert the mini-spec into 3-7 vertical implementation slices.

## When to use

Use when `SPEC.md` exists and implementation needs a short, ordered path.

## Inputs

- `SPEC.md`
- `CONTEXT.md`
- Existing repo structure
- Available verification commands

## Workflow

1. Identify the smallest end-to-end behavior.
2. Create 3-7 slices that each produce observable behavior.
3. Make every slice independently verifiable.
4. Keep each slice to the fewest files possible.
5. Avoid horizontal architecture-only tasks unless required.
6. Record dependencies, risks, and verification strategy.
7. Write `PLAN.md` and `TODO.md`.

## Outputs

- `PLAN.md`
- `TODO.md`

## Stop conditions

- Each task has a visible result and a check.
- Planning reveals a missing spec decision.

## Anti-patterns

- Planning all backend, then all frontend, then all tests.
- Creating broad tasks that cannot be finished in one session.
- Treating setup work as progress when no behavior changes.
