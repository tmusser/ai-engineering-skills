---
name: ceremony-budget
description: Choose the smallest workflow that still buys back enough attention and safety for the task.
---

# Ceremony Budget

## Purpose

Spend ceremony only when it buys back attention or safety. Route a task to a
workflow that replaces the default larger route; do not append a second process
contract.

## When to use

Use when the safe route is not already obvious. If the task or wrapper already
supplies an execution-sized route, use it without re-deriving the route.

## Inputs

- User request and any task-wrapper instructions
- Scope boundary and expected blast radius
- Verification target and failure risk
- Ambiguity, irreversibility, and resume risk

## Workflow

1. Check whether the task is bounded, reversible, and already explicit.
2. Identify the concrete implementation, reproduction, or inspection action and
   its proof target.
3. Choose the lowest level that protects the actual failure mode.
4. Select one replacement route and name only the missing guard, if any.
5. Start the next action immediately once the boundary and proof target are clear.

### Replacement rule

Ceremony budget selects a route that replaces the default larger workflow. Do not
regenerate the full route after a wrapper has already made it explicit. It must
not:

- append a second workflow contract to an already explicit route
- restate task-wrapper instructions
- invoke several skills merely because they are available
- require a budget ledger merely to prove ceremony was budgeted
- create process work whose only purpose is documenting the process choice

When an existing route is sufficient, prefer:

```text
Route already explicit; no additional ceremony block needed.
```

If one guard is missing, provide only that delta:

```text
Route already explicit.
Missing guard: stop after verification and required proof pass.
Next action: implement the named seam.
```

### Startup discipline

For Level 0 and Level 1, do not create a durable planning artifact by default or
run commands solely to document route selection. Identify the concrete action,
then begin it once the boundary and proof target are clear.

For Level 2, allow one compact acceptance block only when real ambiguity exists.
Implementation must follow immediately; do not create secondary artifacts before
the first implementation attempt.

Level 3 may retain fuller safeguards when the risk genuinely warrants them.

## Outputs

Use at most this six-line block, and omit it when the existing route is enough:

```text
CEREMONY ROUTE
Level: 0 | 1 | 2 | 3
Next action: ...
Use: ...
Skip: ...
Proof and stop: ...
```

Do not create `CEREMONY_BUDGET.md` or a budget ledger by default.

### Level guidance

- Level 0: direct patch -> one sanity check -> stop
- Level 1: inline boundary -> build-one -> targeted verify -> stop
- Level 2: compact mini-spec -> build-one -> targeted test -> verify-contract -> stop
- Level 3: fuller guarded route for genuinely high-risk, multi-slice, or
  decision-impacting work

Use `handoff` only when another session actually needs to resume, work remains
unresolved, or durable continuation state buys real safety. It is not automatic.

## Stop conditions

Stop when all are true:

1. required verification has passed
2. required proof is valid
3. no named acceptance criterion or risk remains unresolved

After that, do not rerun an already passing proof validator without a concrete
reason, repeat Git or status commands for reassurance, rewrite valid artifacts for
style, continue because turns remain, add a ceremony retrospective, or expand
verification beyond the named risk without evidence that it is needed.

## Failure discipline

After a targeted check fails:

1. inspect the first actionable traceback or mismatch
2. inspect the actual import, call, or data path implicated by the failure
3. make the smallest related correction
4. rerun the narrow check
5. escalate ceremony only if the failure reveals genuine ambiguity, broader
   scope, or higher risk

Do not respond to one failed check by generating additional planning artifacts.

## Anti-patterns

- Treating more artifacts as automatically better process.
- Making the six-line block mandatory when no route delta is needed.
- Deriving a full route after a wrapper has already made it explicit.
- Requiring `scope-freeze`, `handoff`, a ledger, or a durable artifact for every
  Level 1 task.
- Stopping before required proof is valid.
- Using Level 0 or 1 when the task is decision-impacting or genuinely unsafe to
  resume without durable state.
