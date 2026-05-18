---
name: checklist-mini
description: Validate a mini-spec before planning.
---

# Checklist Mini

## Purpose

Validate a mini-spec before planning.

## When to use

Use after `mini-spec` and before `thin-plan`, especially when the next step would turn unclear requirements into implementation tasks.

## Inputs

- `SPEC.md`
- `CONTEXT.md` if available
- Known commands
- Known constraints
- Open questions

## Workflow

1. Check that unresolved ambiguity is marked with `[NEEDS CLARIFICATION: ...]`.
2. Check that acceptance criteria are observable.
3. Check that success criteria are measurable.
4. Check that non-goals are explicit.
5. Check that a verification demo exists.
6. Check that a scope boundary can be defined.
7. Check that speculative features are absent.
8. Update `CHECKLIST.md` with pass, fail, or needs-clarification notes.

## Outputs

- `CHECKLIST.md`
- Spec readiness judgment
- Blocking clarification notes
- Safe next step

## Stop conditions

- The mini-spec is ready for thin planning.
- A blocking ambiguity must be clarified before planning.

## Anti-patterns

- Planning from vague acceptance criteria.
- Treating missing non-goals as harmless.
- Letting speculative features enter the first implementation plan.
