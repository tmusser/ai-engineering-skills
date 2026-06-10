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
7. Define clear stop condition.
8. Note that reads/searches are allowed unless explicitly forbidden.

## Outputs

**Canonical output block:**
````

SCOPE FREEZE
Task: ...
Allowed: src/ui/settings/, tests/ui/settings_test.py
Read-only: src/core/
Forbidden: changing any other UI components, database schema, or build config
Max files: 4
Allowed commands: git status, pytest, etc.
Stop when: toggle works in UI + tests pass

```

## Success looks like

The example block above.

## Stop conditions

- Scope is narrow enough for safe implementation.
- Task requires changes outside boundary → pause and renegotiate.

## Anti-patterns

- Roaming the entire repo for a small fix.
- Expanding scope because "nearby code looked easy."
- Running write commands before boundary is agreed.
- Forbidding necessary discovery reads.
