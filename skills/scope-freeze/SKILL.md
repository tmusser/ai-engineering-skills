---
name: scope-freeze
description: Explicitly limit blast radius before any implementation or file changes.
---

# Scope Freeze

## Purpose

Prevent uncontrolled changes by defining a narrow, enforceable boundary. This freezes **write scope**, not discovery.

## When to use

Immediately before editing files or running state-changing commands.

## Inputs

- SPEC.md / PLAN.md / TODO.md
- Selected task
- Current repo state

## Workflow

1. Name the exact task.
2. List **allowed** files/folders.
3. List **read-only** files/folders.
4. List **forbidden** operations.
5. Set max files/lines changed (if helpful).
6. List allowed commands.
7. List compatibility seams and test-integrity triggers before editing.
8. Define clear stop condition.
9. Note that reads/searches are allowed unless explicitly forbidden.

## Outputs

**Canonical output block:**

```text
SCOPE FREEZE
Task: ...
Allowed writes: ...
Read-only: ...
Forbidden: ...

Compatibility seams to preserve:
- Public imports / APIs: ...
- CLI behavior: ...
- Output schema: ...
- Fixture/data meaning: ...
- Existing tests that must remain meaningful: ...

Test integrity:
- Existing tests may be added to: yes/no
- Existing tests may be changed only if: ...

Review required if:
- tests changed
- dependencies changed
- protected paths touched
- compatibility seams changed

Allowed commands: ...
Stop when: ...
Invalid if: ...
```

## Success looks like

The canonical block above.

## Stop conditions

- Scope is narrow enough for safe implementation.
- Task requires changes outside boundary → pause and renegotiate.

## Anti-patterns

- Roaming the entire repo for a small fix.
- Expanding scope because "nearby code looked easy."
- Running write commands before boundary is agreed.
- Forbidding necessary discovery reads.
