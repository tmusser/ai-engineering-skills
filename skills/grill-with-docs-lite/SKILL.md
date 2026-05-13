---
name: grill-with-docs-lite
description: Clarify ambiguous AI-engineering project ideas before specs or code by challenging vague terms, naming assumptions, and updating durable context.
---

# Grill With Docs Lite

## Purpose

Clarify an ambiguous project idea before writing specs or code.

## When to use

Use when the request contains vague terms, missing domain language, unclear success criteria, unknown constraints, or hidden assumptions.

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
