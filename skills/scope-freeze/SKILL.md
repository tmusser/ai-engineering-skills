---
name: scope-freeze
description: Limit an agent's blast radius before implementation by defining allowed files, commands, forbidden operations, and stop conditions.
---

# Scope Freeze

## Purpose

Limit the agent's blast radius before implementation.

## When to use

Use immediately before editing files or running commands that can change project state.

## Inputs

- `SPEC.md`
- `PLAN.md`
- `TODO.md`
- Current repo status
- Selected task

## Workflow

1. Name the selected task.
2. List allowed files and folders.
3. List read-only files and folders.
4. List forbidden operations.
5. Set max files changed.
6. Set max lines changed if useful.
7. List allowed commands.
8. Define the stop condition.

## Outputs

- Scope boundary for the task
- Allowed commands
- Stop condition

## Stop conditions

- The scope is narrow enough to implement safely.
- The selected task requires files or commands outside the approved boundary.

## Anti-patterns

- Letting the agent roam the entire repo for a small fix.
- Expanding scope because nearby code looks tempting.
- Running write commands before the boundary is clear.
