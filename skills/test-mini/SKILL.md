---
name: test-mini
description: Add focused deterministic checks, fixtures, or smoke paths for ML workflows, agents, dashboards, data transforms, and scheduled jobs.
---

# Test Mini

## Purpose

Protect against silent wrongness without adding heavy test ceremony.

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
