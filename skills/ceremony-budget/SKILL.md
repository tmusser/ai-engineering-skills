---
name: ceremony-budget
description: Choose the smallest workflow that still buys back enough attention and safety for the task.
---

# Ceremony Budget

## Purpose

Route a task to the smallest safe workflow before the agent starts creating
artifacts or editing files.

## When to use

Use at the start of a task when it is not obvious whether the work needs no
artifact, a short route, or a fuller workflow.

## Inputs

- User request
- Known constraints
- Expected blast radius
- Verification burden
- Resume or handoff risk
- Decision or irreversibility risk

## Workflow

1. Check whether the task is reversible, bounded, and already unambiguous.
2. Check whether failure would mostly waste time or would affect users, data,
   decisions, compatibility seams, or future sessions.
3. Check whether the task is likely to drift without a scope boundary or explicit
   verification target.
4. Choose the lowest level that still protects against the real failure mode.
5. Select the skill route for that level.
6. Name the skills or artifacts intentionally skipped.
7. Reserve the minimum proof needed before stopping.
8. Stop routing once the decision block is good enough to start the work.

## Outputs

Produce a short routing block. Do not create a durable file by default.

```text
CEREMONY BUDGET
Level: 0 | 1 | 2 | 3
Why: ...
Use: ...
Skip: ...
Proof reserve: ...
Stop rule: ...
```

Level guide:

- Level 0: tiny reversible patch; usually no durable artifact
- Level 1: one bounded slice; inline boundary plus proof
- Level 2: small multi-step or ambiguity-prone slice; compact spec and
  verification
- Level 3: decision-impacting, autonomous, user-facing, risky, or multi-slice
  work; full guarded route

Escalate when:

- ambiguity blocks implementation
- scope is starting to drift
- verification is weak or hand-wavy
- context is likely to be lost before completion
- another session must resume safely
- changes are hard to undo or affect decisions, users, or public seams

De-escalate when:

- the task is a tiny reversible edit
- the route is creating artifacts that are not buying clarity or safety
- one shorter proof path would cover the same risk
- the next skill would only restate what is already explicit

## Stop conditions

- The lowest safe level is chosen.
- The selected route and proof reserve are explicit.
- Do not continue routing once the next step is clear.

## Anti-patterns

- Treating more artifacts as automatically better process.
- Creating `SPEC.md`, `PLAN.md`, or `HANDOFF.md` for a trivial reversible fix.
- Creating `CEREMONY_BUDGET.md` by default.
- Escalating because the repo has a skill available, not because the task needs it.
- Using Level 0 or 1 when the task is decision-impacting or hard to resume safely.
