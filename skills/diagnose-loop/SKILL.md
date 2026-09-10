---
name: diagnose-loop
description: Diagnose reproducible failures with hypothesis-driven fixes and bounded retries.
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
6. Name one active hypothesis and the observation that would falsify it; apply the smallest fix that tests it.
7. Add a regression check if possible.
8. Rerun the original failing command.
9. Rerun relevant verification. An improved signal is not completion; the original failure and compatibility checks must pass.
10. Before a second repair attempt, count the initial attempt and define the retry contract: fixed input/evaluator identities, acceptance threshold, total attempt limit, consecutive no-progress limit, revert rule, ledger location, and review trigger. If incomplete, stop with `REVIEW_REQUIRED`; the initial bounded diagnosis does not require a separate loop artifact.
11. Record each started attempt, including failed commands and interrupted attempts: hypothesis, artifact state, evidence, outcome, and consumed budget. Change the next hypothesis only when the evidence supports it. Unchanged or worse results and tool errors consume the no-progress budget; improvement does not reset the total budget.
12. Stop at acceptance, either budget limit, an unresolved interruption, or a scope/permission/evaluator change. Preserve the best known state and the failed attempt's evidence; revert only edits owned by this attempt, never unrelated user work. Reconcile uncertain external effects before retrying.
13. On resume, carry forward the same loop identity, ledger, input/evaluator identities, consumed budget, and stop reason. A fresh session or subtask does not grant new attempts. Renew a spent budget or change the evaluator only through an explicit contract revision; preserve the prior ledger.

## Outputs

- Root-cause note
- Smallest fix
- Regression check when possible
- Rerun results
- For repeated repairs: compact attempt ledger, remaining budget, and stop reason

## Stop conditions

- The original failure is fixed and verified.
- The failure cannot be reproduced.
- The next step requires a product or data decision.
- Retry limits are reached, evidence is stale, or an interrupted attempt has unresolved effects.

## Anti-patterns

- Repeating the same failed fix without a new falsifiable hypothesis.
- Weakening tests, changing the evaluator, or resetting counters to make progress appear green.
- Randomly editing files before reproducing the bug.
- Fixing symptoms without naming the failing case.
- Adding noisy instrumentation and leaving it behind.
