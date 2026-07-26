---
name: mini-spec
description: Create a compact SPEC.md that prevents premature agreement by defining intent, non-goals, likely failure modes, a spec ceiling, and verification evidence.
---

# Mini Spec

## Purpose

Create the smallest useful `SPEC.md` that clarifies intent, names the likely failure mode, and gives the agent a verifiable target before planning or implementation.

The spec is both a floor and a ceiling: acceptance criteria define what must happen; non-goals, constraints, and invalid-if rules bound what must not be added.

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
5. Define the spec ceiling: do not add behavior, interfaces, refactors, dependencies, or adjacent cleanup beyond what is required to satisfy the acceptance criteria.
6. List likely failure modes and name the primary failure mode for this slice.
7. Record constraints.
8. List run, test, build, and verification commands.
9. Sketch project structure.
10. Define the smallest verification demo.
11. Record open questions.
12. When applicable, name compatibility seams that must remain import-compatible or output-compatible.
13. When applicable, record invalid-if constraints that would make the slice non-viable.
14. For delegated, autonomous, multi-session, or replanned work, optionally record a contract ID, parent ID, base commit, issue time, and replan reason.
15. If satisfying the task requires behavior outside the ceiling, update or renegotiate the spec before implementing that expansion.

## Outputs

- `SPEC.md`
- Explicit acceptance criteria
- Explicit non-goals
- Explicit spec ceiling
- Likely failure modes
- Verification demo
- Optional contract identity when traceability buys back safety

## Compatibility seams to preserve

When applicable, list behavior that must remain import-compatible or output-compatible.

- Public imports / APIs: _TBD_
- CLI commands / flags: _TBD_
- JSON/schema/output contracts: _TBD_
- Existing tests whose meaning must remain valid: _TBD_
- Data/fixture semantics: _TBD_

## Invalid if

- breaks a named compatibility seam
- implements an explicit non-goal or adds adjacent behavior not required by an acceptance criterion
- weakens or rewrites existing tests merely to fit the implementation
- changes fixture/source data without explicit approval
- preserves behavior only through a new alternate path while breaking the old path
- changes forbidden/protected files
- adds dependencies or framework changes outside scope

## Stop conditions

- The spec is under 100 lines unless risk justifies more.
- The next implementation slice is clear.
- The behavioral ceiling is clear enough to distinguish necessary support work from optional extras.
- Unresolved questions are recorded instead of hidden.

## Anti-patterns

- Turning a small POC into a full product requirements document.
- Adding speculative future features.
- Treating unrequested "helpful" behavior as bonus work instead of scope expansion.
- Writing vague acceptance criteria that cannot be verified.
- Assigning contract identifiers to tiny edits merely to create process metadata.
