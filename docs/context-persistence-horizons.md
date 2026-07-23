# Context Persistence Horizons

`ai-engineering-skills` treats durable task state as a distinct layer between an
agent's active working context and a broader long-term memory system.

The three horizons solve different failure modes and should not be collapsed into
one artifact or retrieval strategy.

## The three horizons

| Horizon | Typical lifetime | Canonical state | Primary job |
| --- | --- | --- | --- |
| Working state | One active step or session | Current prompt, compact context packet, active hypothesis | Keep the immediate action coherent |
| Task state | Multiple sessions or agents | `SPEC.md`, `PLAN.md`, `VERIFY.md`, `HANDOFF.md` | Preserve the contract, proof, and safe continuation state |
| Knowledge state | Multiple projects and long periods | Curated memory system with provenance and conflict handling | Preserve stable facts, preferences, and reusable knowledge |

## Working state

Working state is intentionally disposable. It may include:

- the current implementation slice
- a bounded context packet
- one active debugging hypothesis
- the next command or verification gate

Use `context-check` and context hydration to keep this layer small. Do not treat the
full chat transcript as durable project state.

## Task state

Task state is the layer this repository owns.

- `SPEC.md` records the current contract and invalidators.
- `PLAN.md` records an optional implementation shape.
- `VERIFY.md` records auditable evidence and remaining uncertainty.
- `HANDOFF.md` records the resume packet when another session must continue.

Current task artifacts outrank remembered summaries when they disagree. A fresh
session should be able to resume from these files without replaying the full chat.

## Knowledge state

Knowledge state is broader than a coding-task handoff. It may retain stable user,
project, or organizational knowledge across many tasks.

A long-term memory system should track source, confidence, recency, replacement, and
conflict. This repository does not provide that database or retrieval runtime.

Do not silently promote temporary task guesses into long-term knowledge. Promote only
stable facts that have an explicit source and a reason to survive the current task.

## Promotion rules

Move information upward only when the longer retention period buys real value.

```text
working state -> task state -> knowledge state
```

- Promote working state to task state when another session needs it, verification
  depends on it, or losing it would make continuation unsafe.
- Promote task state to knowledge state only when the information is stable across
  projects or repeated future work.
- Keep transient logs, abandoned hypotheses, and chat narration at the working-state
  horizon.
- Preserve provenance when promoting information. A summary without a source should
  not silently become authoritative.

## Failure boundaries

- `HANDOFF.md` is not a transcript archive.
- A context packet is not a system of record.
- A long-term memory hit does not override the current `SPEC.md` or `VERIFY.md`.
- More retained context is not automatically better context.
- Durable state should be compact enough to inspect and specific enough to verify.

## Practical routing

Use the smallest persistence horizon that protects the actual risk:

- Tiny reversible edit: working state only.
- Multi-session coding task: durable task artifacts.
- Stable cross-project fact or preference: external knowledge memory with provenance.

This separation keeps the repository focused: it provides durable, reviewable task
state while remaining compatible with richer memory and runtime systems underneath it.
