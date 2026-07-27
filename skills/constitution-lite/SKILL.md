---
name: constitution-lite
description: Define a tiny set of stable, non-negotiable agent authority boundaries for repeated or delegated work without duplicating CLAUDE.md, AGENTS.md, or task specs.
---

# Constitution Lite

## Purpose

Record only the durable rules that constrain what an agent may decide or do across
multiple tasks. This is an authority boundary, not a project handbook.

Project instructions are not constitution rules. Architecture notes, repo layout,
commands, coding style, naming conventions, framework choices, and ordinary team
preferences belong in native project instructions such as `CLAUDE.md` or `AGENTS.md`.
Task-specific requirements belong in `SPEC.md`, `scope-freeze`, or `SHIP.md`.

## When to use

Use when repeated, delegated, scheduled, or autonomous work needs a small set of
stable constraints that should survive across tasks, such as:

- human approval before destructive or external side effects
- protected production, data, credential, or customer boundaries
- tests or evidence that an agent may not weaken to make work pass
- decisions an agent is never authorized to make alone

Skip this skill when the need is only project onboarding, commands, architecture,
style, a temporary implementation constraint, or one task's acceptance criteria.

## Inputs

- Existing `CLAUDE.md`, `AGENTS.md`, or equivalent project instructions if present
- Stable risk and authority boundaries
- Protected resources, environments, data, or interfaces
- Human approval requirements
- Existing task or shipping controls that should not be duplicated

## Workflow

1. Read existing project instructions first. Do not copy their conventions into the constitution.
2. List candidate cross-task rules.
3. Keep a candidate only when violating it should require a human decision, explicit review, or a hard stop across more than one task.
4. Classify each retained rule as `MUST`, `MUST NOT`, or `HUMAN GATE`.
5. Make each rule observable where possible: name the protected resource, forbidden action, approval event, or evidence requirement.
6. Remove architecture preferences, commands, style guidance, framework choices, and task-local constraints.
7. If the constitution conflicts with live project instructions or a task contract, stop and ask for a human decision. Do not silently choose an authority winner.
8. Name who may amend the constitution and how the amendment is approved.
9. Keep the artifact short enough to scan before delegated work.

### Authority boundary

`CONSTITUTION.md` is a workflow artifact. It does not override system instructions,
organization policy, platform permissions, sandboxing, or runtime safety controls.
It also does not grant an agent permission merely because an action is absent from
the constitution.

Use the constitution to narrow delegated authority, not to expand it.

## Outputs

- `CONSTITUTION.md`
- Non-negotiable `MUST` / `MUST NOT` invariants
- Explicit `HUMAN GATE` decisions
- Protected resource or data boundaries when relevant
- Amendment owner and process

**Canonical shape:**

```text
CONSTITUTION
MUST: ...
MUST NOT: ...
HUMAN GATE: ...
Protected boundary: ...
Conflict rule: stop and ask for a human decision
Amendment owner: ...
```

## Stop conditions

- Every retained rule changes agent authority across multiple tasks.
- Ordinary project instructions and task-local constraints have been removed.
- Human approval gates are explicit.
- A conflict has been surfaced rather than silently resolved.
- The artifact is small enough to scan before delegated work.

## Anti-patterns

- Rewriting `CLAUDE.md` or `AGENTS.md` as `CONSTITUTION.md`.
- Filling the artifact with architecture, commands, coding style, or naming conventions.
- Promoting temporary preferences into permanent governance.
- Treating the constitution as permission to perform otherwise unauthorized actions.
- Adding aspirational principles that cannot change an agent decision.
- Silently resolving conflicts between durable governance and a task contract.
