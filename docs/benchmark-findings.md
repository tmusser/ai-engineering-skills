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
| Task 7 — Dashboard Export Scope Pressure | Stronger settings saturated on behavior; weaker settings exposed API seam and test-integrity failures. | The best hardening move was sharper invalidation, not heavier skills. |

## Claim boundary

Supported:

- auditability
- verification discipline
- resumability

Not supported:

- broad skill superiority
- guaranteed correctness
- universal behavior improvement

The Task 7 follow-up suggested the highest-leverage improvement was not heavier
skills, but sharper invalidation: compatibility probes, diff guards, and
`REVIEW_REQUIRED` states.

## Why it matters

The benchmark is useful because it exposes where the current skills still need better
recipes, especially around compatibility seams, evidence integrity, and recovery
state.
