---
name: mini-spec
description: Create a compact, reference-first SPEC.md that defines the task-specific delta, non-goals, likely failure modes, spec ceiling, and verification target without paraphrasing richer authoritative sources.
---

# Mini Spec

## Purpose

Create the smallest useful `SPEC.md` that clarifies intent, names the likely failure mode, and gives the agent a verifiable target before planning or implementation.

The spec is both a floor and a ceiling: acceptance criteria define what must happen; non-goals, constraints, and invalid-if rules bound what must not be added.

When a high-fidelity reference already expresses behavior well, point to it instead of rewriting it into a weaker prose summary. The spec should capture the task-specific delta, authority boundary, and proof target around that reference.

## When to use

Use when a project or feature is clear enough to define before implementation.

## Inputs

- Clarified request
- `CONTEXT.md` if available
- Constraints
- Known commands
- Acceptance criteria or desired behavior
- Authoritative references when available: existing tests, code, schemas, HTML/mockups, rubrics, external specs, or a source implementation to port

## Reference-first rule

Prefer the richest authoritative source that already expresses the intended behavior.

For each reference, record:

- the exact file, test, artifact, URL, or symbol
- what behavior or decision it governs
- the task-specific delta, if this slice intentionally differs

Do not restate a detailed test suite, implementation, mockup, or rubric line by line merely to make the spec self-contained. Keep the reference available and write only the interpretation needed to bound this task.

If the user request and an authoritative reference conflict, surface the conflict as an explicit decision or open question. Do not silently reconcile them.

## Workflow

1. State the objective.
2. Identify the user or use case.
3. Identify authoritative references and what each one governs.
4. Record the task-specific delta from those references; use `none` when the reference is the intended contract as-is.
5. Define observable acceptance criteria, pointing to authoritative references where they already encode the behavior precisely.
6. Record non-goals.
7. Define the spec ceiling: do not add behavior, interfaces, refactors, dependencies, or adjacent cleanup beyond what is required to satisfy the acceptance criteria and reference-backed delta.
8. List likely failure modes and name the primary failure mode for this slice.
9. Record constraints.
10. List only non-obvious run, test, build, and verification commands that matter to the slice.
11. Define the smallest verification demo.
12. Record open questions and reference conflicts instead of inventing a resolution.
13. When applicable, name compatibility seams that must remain import-compatible or output-compatible.
14. When applicable, record invalid-if constraints that would make the slice non-viable.
15. For delegated, autonomous, multi-session, or replanned work, optionally record a contract ID, parent ID, base commit, issue time, and replan reason.
16. If satisfying the task requires behavior outside the ceiling or contradicts an authoritative reference, update or renegotiate the spec before implementing that expansion.

## Outputs

- `SPEC.md`
- Authoritative references + what they govern
- Task-specific delta
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
- silently contradicts an authoritative reference without recording the intended delta
- weakens or rewrites existing tests merely to fit the implementation
- changes fixture/source data without explicit approval
- preserves behavior only through a new alternate path while breaking the old path
- changes forbidden/protected files
- adds dependencies or framework changes outside scope

## Stop conditions

- The spec is under 100 lines unless risk justifies more.
- The next implementation slice is clear.
- Reference authority and any task-specific delta are explicit when references exist.
- The behavioral ceiling is clear enough to distinguish necessary support work from optional extras.
- Unresolved questions are recorded instead of hidden.

## Anti-patterns

- Turning a small POC into a full product requirements document.
- Rewriting a high-fidelity test, implementation, mockup, or rubric into a lossy prose duplicate.
- Sketching repository structure the agent can inspect directly unless the structure itself is a task constraint.
- Adding speculative future features.
- Treating unrequested "helpful" behavior as bonus work instead of scope expansion.
- Writing vague acceptance criteria that cannot be verified.
- Assigning contract identifiers to tiny edits merely to create process metadata.
