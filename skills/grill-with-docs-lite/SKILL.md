---
name: grill-with-docs-lite
description: Run a short boundary-grilling pass for small AI-engineering tasks, clarifying intent, non-goals, terms, constraints, and readiness before mini-spec.
---

# Grill With Docs Lite

## Purpose

Clarify whether a small AI-engineering task is ready for `mini-spec` by resolving only the ambiguity that could cause wrong work, scope creep, or unsafe implementation.

## When to use

Use when a request is probably small enough to move quickly, but contains vague terms, unclear success criteria, unknown constraints, hidden assumptions, or boundary risk.

Use a fuller domain-model grilling workflow instead when the work depends on existing glossary terms, ADRs, cross-context architecture, or deep codebase/domain alignment.

## Inputs

- User request
- Existing notes or docs
- Relevant repo files
- `CONTEXT.md` if present

## Workflow

1. Restate the request in concrete terms.
2. Challenge vague words such as "better", "fast", "simple", or "automated".
3. Identify domain terms and define them in working language.
4. Surface assumptions, decisions, non-goals, and external constraints.
5. Ask only questions that block safe progress.
6. Update `CONTEXT.md`.
7. Give a readiness judgment: ready, ready with assumptions, or blocked.

## Outputs

- Clarified request
- Domain terms
- Decisions
- Assumptions
- Non-goals
- Unresolved questions
- Readiness judgment

## Stop conditions

- The problem language is clear enough for a mini-spec.
- A blocking question cannot be answered from available context.

## Anti-patterns

- Starting implementation before the problem language is clear.
- Treating unclear business terms as obvious.
- Asking broad questions when a narrow assumption would work.
- Turning a short readiness gate into a full domain-model interrogation when the next slice only needs bounded intent.
