# Benchmark Findings

This repo is paired with
[`agent-workflow-bench`](https://github.com/tmusser/agent-workflow-bench), a small
standalone benchmark for agent skills, verification artifacts, and fresh-session
resumability.

The benchmark does not claim broad pass-rate superiority. It asks a narrower
question: when an agent finishes messy technical work, does it leave enough verified
context for another fresh session to trust, audit, and continue it?

## What the pilot showed

| Task | What happened | What it showed |
| --- | --- | --- |
| Task 4 — Impossible Churn Regression | Functional fixes landed; skill-routed runs left `BUGS.md`, `VERIFY.md`, and `HANDOFF.md` artifacts. | Durable artifacts help audit and resumability. |
| Task 5 — Fake Data Campaign Lift Trust | Both paths passed public checks but missed hidden denominator / leakage traps. | Clearer audit trails help inspection, but do not guarantee correctness. |
| Task 7 — Dashboard Export Scope Pressure | Scope pressure exposed the difference between too much ceremony, too little ceremony, and targeted proof reserve. In the observed stripped-resume rerun, the functional solution was preserved and the benchmark harness produced valid deterministic proof artifacts. | The useful move was not heavier process by default. It was selecting the smallest route that protected compatibility seams, proof quality, and fresh-session resume safety. |

## Current project claims

Benchmark-supported:

- auditability
- verification discipline
- fresh-session resumability

Repo-supported:

- optional ceremony routing for choosing a smaller or larger workflow before work
- benchmark-informed workflow improvement through `ceremony-budget`

The strongest current claim is:

```text
ai-engineering-skills helps coding agents leave bounded, verified, resumable work
artifacts, and now includes ceremony budgeting to choose the smallest workflow that
still protects scope, proof, and resume safety.
```

## Open claim ledger

[`CLAIMS.md`](../CLAIMS.md) preserves broader assertions that are important enough to test
but are **not yet current project claims**. Each entry freezes a scope and support/refute rule
before additional evidence is used to judge it.

An `OPEN` claim is not promoted by repetition, plausibility, or a favorable anecdote. It becomes
`SUPPORTED` only when its recorded judge contract is met. `REFUTED` and `INCONCLUSIVE` are
first-class outcomes too.

The ledger intentionally excludes universal assertions that are too broad to adjudicate in a
practical benchmark. Narrow them to a falsifiable scope before preserving them as claims.

## Claim boundary

Not supported:

- broad skill superiority
- guaranteed correctness
- universal behavior improvement
- automatic selection of the perfect amount of process
- universal fresh-session robustness across tasks, models, and seeds

Use Task 7 as motivating evidence, not as proof of general superiority. The Task 7
follow-up suggested the highest-leverage improvement was not heavier skills, but
sharper invalidation and better route selection: compatibility probes, diff guards,
proof reserve, verify-before-edit resume behavior, and deterministic proof
finalization.

## Why it matters

The benchmark is useful because it exposes where the current skills still need better
recipes, especially around compatibility seams, evidence integrity, recovery state,
and knowing when not to use heavier parts of the workflow.
