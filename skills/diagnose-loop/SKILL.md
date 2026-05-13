---
name: diagnose-loop
description: Debug failures systematically by reproducing the issue, listing hypotheses, applying the smallest fix, and rerunning verification.
---

# Diagnose Loop

## Purpose

Debug failures systematically.

## When to use

Use when a command fails, behavior is wrong, a test regresses, or output does not match the spec.

## Inputs

- Failure report
- Exact command or reproduction case
- Recent changes
- Logs, traces, or output

## Workflow

1. Freeze feature work.
2. Reproduce the failure.
3. Identify the exact failing command or case.
4. List hypotheses.
5. Instrument minimally.
6. Apply the smallest fix.
7. Add a regression check if possible.
8. Rerun the original failing command.
9. Rerun relevant verification.

## Outputs

- Root-cause note
- Smallest fix
- Regression check when possible
- Rerun results

## Stop conditions

- The original failure is fixed and verified.
- The failure cannot be reproduced.
- The next step requires a product or data decision.

## Anti-patterns

- Randomly editing files before reproducing the bug.
- Fixing symptoms without naming the failing case.
- Adding noisy instrumentation and leaving it behind.
