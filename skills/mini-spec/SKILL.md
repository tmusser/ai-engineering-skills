---
name: mini-spec
description: Create a compact SPEC.md for fast solo AI-engineering projects when the goal is clear enough to define behavior, constraints, and verification without full PRD ceremony.
---

# Mini Spec

## Purpose

Create a small but durable `SPEC.md` for fast solo projects.

## When to use

Use after the project goal is clear enough to define behavior, constraints, and verification.

## Inputs

- Clarified request
- `CONTEXT.md`
- Existing project files
- Known commands and constraints

## Workflow

1. Write the objective in one or two sentences.
2. Name the user or use case.
3. Define acceptance criteria as observable outcomes.
4. Record non-goals and constraints.
5. List commands needed to build, test, run, or inspect.
6. Sketch the expected project structure.
7. Define a verification demo.
8. Keep the spec under 100 lines unless the risk justifies more.

## Outputs

- `SPEC.md` with Objective, User / use case, Acceptance criteria, Non-goals, Constraints, Commands, Project structure, Verification demo, and Open questions

## Stop conditions

- The spec is clear enough to plan 3-7 vertical slices.
- A missing decision would change the project shape.

## Anti-patterns

- Turning a small POC into a full product requirements document.
- Writing acceptance criteria that cannot be verified.
- Hiding important constraints in chat history.
