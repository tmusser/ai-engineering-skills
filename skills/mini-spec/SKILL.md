---
name: mini-spec
description: Create a compact SPEC.md for fast solo AI-engineering projects when the goal is clear enough to define behavior, constraints, and verification without full PRD ceremony.
---

# Mini Spec

## Purpose

Create a small but durable `SPEC.md` for fast solo projects.

## When to use

Use when a project or feature is clear enough to define, but too important to implement from a vague chat request.

## Inputs

- Clarified request
- `CONTEXT.md` if available
- Constraints
- Known commands
- Acceptance criteria or desired behavior

## Workflow

1. State the objective.
2. Identify the user or use case.
3. Define observable acceptance criteria.
4. Record non-goals.
5. Record constraints.
6. List run, test, build, and verification commands.
7. Sketch project structure.
8. Define the smallest verification demo.
9. Record open questions.

## Outputs

- `SPEC.md`
- Explicit acceptance criteria
- Explicit non-goals
- Verification demo

## Stop conditions

- The spec is under 100 lines unless risk justifies more.
- The next implementation slice is clear.
- Unresolved questions are recorded instead of hidden.

## Anti-patterns

- Turning a small POC into a full product requirements document.
- Adding speculative future features.
- Writing vague acceptance criteria that cannot be verified.
