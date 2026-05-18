---
name: constitution-lite
description: Create a small set of project rules before repeated agent work.
---

# Constitution Lite

## Purpose

Create a small set of project rules before repeated agent work.

## When to use

Use when a project will need multiple agent sessions, multiple implementation slices, or repeated decisions about quality, data, autonomy, and simplicity.

## Inputs

- Project goal
- Existing `CONTEXT.md` or notes
- Known technical constraints
- Team or owner preferences
- Risk areas

## Workflow

1. Define engineering principles.
2. Define testing principles.
3. Define data, model, or dashboard principles if relevant.
4. Define agent autonomy boundaries.
5. Define simplicity rules.
6. List forbidden patterns.
7. Define how rules may be amended.
8. Keep the result short enough to read before implementation.

## Outputs

- `CONSTITUTION.md`
- Engineering principles
- Testing principles
- Data/model/dashboard principles
- Agent autonomy boundaries
- Simplicity rules
- Forbidden patterns
- Amendment process

## Stop conditions

- The rules are clear enough to guide repeated agent work.
- A principle conflicts with the project goal and needs a human decision.

## Anti-patterns

- Creating a policy document too long to use.
- Adding rules that cannot change implementation choices.
- Treating temporary preferences as permanent principles.
