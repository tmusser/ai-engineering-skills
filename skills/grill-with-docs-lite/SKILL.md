---
name: grill-with-docs-lite
description: Run a bounded docs-grounded contradiction hunt before mini-spec, separating source facts from decisions, assumptions, and blockers without building a domain model.
---

# Grill With Docs Lite

## Purpose

Turn a fuzzy but small AI-engineering request into a compact, source-grounded clarification delta for `mini-spec`.

This is not an exhaustive interview or a domain-modeling workflow. It does not build a glossary, write ADRs, or walk every branch of a decision tree. Its job is to find the few contradictions or unknowns that could make the next bounded slice wrong.

## When to use

Use when a request is probably small enough to move quickly, relevant docs or repo evidence exist, but success criteria, constraints, terminology, or assumptions may conflict with that evidence.

Use a fuller domain-model or architecture workflow instead when the work requires canonical vocabulary, multiple hard-to-reverse architectural decisions, cross-context modeling, or an open-ended decision tree.

## Inputs

- User request
- Existing notes or docs
- Relevant repo files
- `CONTEXT.md` if present

## Workflow

1. Read the smallest relevant source set before asking questions.
2. Extract only facts that can change scope, acceptance, compatibility, or verification.
3. Classify each unresolved point as:
   - `FACT` — supported by a source; include the file/path or other locator.
   - `DECISION` — requires an explicit user/product choice.
   - `ASSUMPTION` — a reversible working default that can be stated safely.
   - `UNKNOWN` — missing evidence that blocks safe progress.
4. Hunt for contradictions between the request, source facts, non-goals, constraints, and existing behavior.
5. Answer from docs or code when the repository can settle the point; do not ask the user to repeat discoverable facts.
6. Ask only blocking questions. Default question budget: at most 3. Ask one at a time only when an answer can change the next question.
7. Do not update `CONTEXT.md`, create glossary entries, or write ADRs as part of this skill.
8. Emit one compact **CLARIFICATION DELTA** for `mini-spec` and stop.
9. If the ambiguity cannot fit the bounded question budget without losing important decisions, route to a fuller clarification/domain-model workflow instead of expanding this skill.

## Outputs

Use this compact shape:

```text
CLARIFICATION DELTA
Objective: ...
Source-backed facts:
- FACT — ... [path/locator]
Decisions:
- ...
Assumptions:
- ...
Non-goals / boundaries:
- ...
Open blockers:
- ... | none
Mini-spec readiness: ready | ready with assumptions | blocked
```

The delta is input to `mini-spec`; it is not a replacement for `SPEC.md`.

## Success looks like

- The next slice is clearer because contradictions were resolved, not because the interview was exhaustive.
- Source-backed facts are distinguishable from choices and assumptions.
- The agent asked no question that available docs or code could answer.
- The result is compact enough to feed directly into `mini-spec`.

## Stop conditions

- The problem is clear enough for `mini-spec`.
- The default question budget is exhausted and important ambiguity remains → route to a fuller workflow.
- A blocking unknown cannot be resolved from available evidence.

## Anti-patterns

- Building a glossary or ADR trail during a lite pre-spec pass.
- Walking every branch of a decision tree after the bounded slice is already clear.
- Asking broad questions when a narrow assumption would safely unblock progress.
- Treating source silence as a fact.
- Restating whole documents instead of extracting decision-relevant evidence.
- Asking the user for information the repository can answer.
- Starting implementation before the clarification delta is ready for `mini-spec`.
