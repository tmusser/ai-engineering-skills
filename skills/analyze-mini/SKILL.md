---
name: analyze-mini
description: Risk-triggered consistency checkpoint that detects when task artifacts, assumptions, or verification no longer support a safe build decision.
---

# Analyze Mini

## Purpose

Prevent stale or contradictory reasoning from crossing into `build-one` without turning analysis into a routine gate.

`analyze-mini` is conditional. The cheap safeguard is an eligibility check over artifacts already being read for build or handoff. Run the full skill only when that check finds a meaningful trigger.

## When to use

Run a full analysis when one or more of these are true:

- `HANDOFF.md` marks analysis `REQUIRED` or `STALE`
- task-defining inputs changed since the last `FRESH` analysis: `SPEC.md`, `PLAN.md`, `TODO.md`, scope-freeze notes, selected task, or a decision/assumption that changes implementation
- the selected task cannot be traced cleanly from acceptance criterion to implementation slice to verification
- an unresolved decision or assumption could materially change implementation shape
- compatibility seams, data/metric semantics, or cross-boundary behavior create interpretation risk
- failed verification caused the implementation strategy or plan to change
- reconciling a stale handoff changed the live task state

Do not run a full analysis merely because the skill is installed, because a handoff is being written, or because no prior analysis exists.

Missing prior analysis is not, by itself, a trigger.

Staleness is event-driven, not time-driven. A checkpoint does not expire just because time passed.

## Inputs

Use the smallest relevant set:

- Selected task
- `SPEC.md`
- `PLAN.md` / `TODO.md` when they exist
- Scope-freeze boundary
- Relevant `HANDOFF.md` state when resuming
- `VERIFY.md` when a failure or changed strategy is part of the trigger
- Only the source files needed to resolve a specific contradiction

## Passive eligibility check

Before invoking the full skill, reuse artifacts already loaded for `build-one` or `handoff` and ask:

1. Did a task-defining input change since the last trustworthy checkpoint?
2. Is there an unresolved decision or assumption that could change the implementation?
3. Can the selected task still map cleanly from acceptance criterion to verification without contradicting a non-goal, spec ceiling, or scope boundary?
4. Did a failed attempt or resume reconciliation create a new implementation uncertainty?

If all answers are no, use `NOT_NEEDED`. Do not perform a broader repo scan just to prove that analysis was skipped.

## Checkpoint states

`Analysis checkpoint: FRESH | NOT_NEEDED | STALE | REQUIRED`

- `FRESH` — a full analysis was run against the current task-defining inputs.
- `NOT_NEEDED` — the cheap eligibility check found no trigger for a full analysis.
- `STALE` — a prior `FRESH` analysis exists, but a task-defining input changed.
- `REQUIRED` — a current trigger exists and a full analysis must run before implementation continues.

`FRESH` and `NOT_NEEDED` permit implementation only when no separate blocker exists.

## Workflow

1. Name the trigger. Do not start with a generic repo review.
2. Identify the smallest artifact delta that could affect the selected task.
3. Map acceptance criterion -> selected task -> verification evidence.
4. Check non-goals, spec ceiling, compatibility seams, and scope-freeze boundaries for contradictions.
5. Check decisions and assumptions that can materially change implementation shape.
6. Separate contradictions from unknowns; do not invent certainty to make the artifacts agree.
7. Make an implementation readiness call: `READY` or `BLOCKED`.
8. Emit a compact checkpoint:

```text
ANALYSIS CHECKPOINT
State: FRESH
Readiness: READY | BLOCKED
Trigger: ...
Inputs reviewed: ...
Finding: ...
Criterion -> task -> proof: ...
Re-run when: ...
```

1. If a handoff is being updated, carry the checkpoint state and reason into `HANDOFF.md`. Otherwise return the compact checkpoint inline.
2. Do not create `ANALYZE.md` for a clean checkpoint. Create or update it only when material findings need durable standalone review or the user explicitly asks for it.

## Outputs

- Compact analysis checkpoint
- `READY` or `BLOCKED` implementation call when full analysis runs
- Material contradictions, unknowns, or verification gaps
- Optional `ANALYZE.md` only when durable standalone findings are justified

## Stop conditions

- `NOT_NEEDED` is justified by the cheap eligibility check, or
- the full analysis establishes a current `FRESH` checkpoint and `READY`, or
- a contradiction or unresolved decision makes readiness `BLOCKED`

## Anti-patterns

- Running `analyze-mini` before every `build-one` merely because it is available.
- Treating a missing prior analysis as analysis debt by default.
- Re-reading the whole repository to decide whether analysis is needed.
- Creating `ANALYZE.md` after every clean consistency check.
- Expiring a valid checkpoint because of elapsed time rather than a state change.
- Keeping a checkpoint `FRESH` after task-defining inputs changed.
- Starting implementation while a `REQUIRED` or `STALE` checkpoint is unresolved.
- Adding complexity because analysis surfaced an interesting adjacent improvement.
