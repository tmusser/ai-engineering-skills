---
name: test-mini
description: Add focused deterministic tests, fixtures, or smoke checks.
---

# Test Mini

## Purpose

Protect against wrong behavior without heavy tests.

## When to use

Use for ML model workflows, agents, dashboards, data transformations, metric calculations, scheduled jobs, and any behavior that can appear to run while being wrong.

## Inputs

- Implemented slice
- Expected behavior
- Available fixtures or examples
- Build/test/run commands

## Workflow

1. Add one deterministic behavior test when possible.
2. Add one fixture or golden example when useful.
3. Add one smoke test or manual verification path.
4. Run exact commands.
5. Record command output and result.
6. Keep tests focused on the changed behavior.

## Test integrity

Prefer adding tests over changing existing tests.

If modifying existing tests:

1. Record the changed test path.
2. State why the old assertion was wrong or incomplete.
3. Name the source of truth.
4. Preserve the prior assertion or replace it intentionally.
5. Mark verification as `REVIEW_REQUIRED` unless the rationale is explicit.

Never weaken tests merely to match the implementation.

## Outputs

- Focused test or fixture
- Smoke path
- Exact command results
- Remaining risk notes

## Stop conditions

- The behavior is proven enough for the task risk.
- No deterministic check is possible without changing the design.

## Anti-patterns

- Only checking that the code runs without checking correctness.
- Adding broad tests unrelated to the changed behavior.
- Hiding manual verification steps in chat.
