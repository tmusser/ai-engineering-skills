---
name: mini-spec
description: Create a compact SPEC.md that prevents premature agreement by defining intent, non-goals, likely failure modes, and verification evidence.
---

# Mini Spec

## Purpose

Create the smallest useful `SPEC.md` that clarifies intent, names the likely failure mode, and gives the agent a verifiable target before planning or implementation.

## When to use

Use when a project or feature is clear enough to define before implementation.

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
5. List likely failure modes and name the primary failure mode for this slice.
6. Record constraints.
7. List run, test, build, and verification commands.
8. Sketch project structure.
9. Define the smallest verification demo.
10. Record open questions.

## Outputs

- `SPEC.md`
- Explicit acceptance criteria
- Explicit non-goals
- Likely failure modes
- Verification demo

## Stop conditions

- The spec is under 100 lines unless risk justifies more.
- The next implementation slice is clear.
- Unresolved questions are recorded instead of hidden.

## Anti-patterns

- Turning a small POC into a full product requirements document.
- Adding speculative future features.
- Writing vague acceptance criteria that cannot be verified.
