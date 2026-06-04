---
name: context-check
description: Detect context drift, rehydration loops, scope creep, active-mode loss, hypothesis sprawl, durable-state gaps, and compaction pressure in small AI-assisted engineering sessions. Use when a thread is getting long, repeated facts are being restated, a task changes shape, debugging has multiple competing hypotheses, handoff or fresh context is mentioned, active modes like lean-mode may need to persist, or the agent may be leaving a bounded vertical-slice workflow. Recommend the smallest corrective action: continue, freeze scope, update durable state, fork, handoff, or restart.
---

# Context Check

## Purpose

Keep AI-engineering sessions cheap, bounded, and durable without adding ceremony.

Detect when the thread is starting to distort execution through rehydration, scope drift, hypothesis sprawl, or missing durable state.

## When to use

Use passively as a guardrail during project work.

Speak only when risk is medium or high, unless the user explicitly invokes `context-check`.

Use when:

- The same facts or premises are being restated.
- The same misconception has been corrected twice.
- Scope, audience, hypothesis, or error class changes.
- Debugging has more than one active hypothesis.
- A handoff, fork, restart, compaction, or fresh context is being considered.
- Active modes may need to survive into another session.
- Important facts still live only in chat.

## Inputs

- Current task and recent conversation.
- Durable files such as `CONTEXT.md`, `SPEC.md`, `PLAN.md`, `TODO.md`, `VERIFY.md`, `DECISIONS.md`, `BUGS.md`, and `HANDOFF.md` if present.
- Current phase, active modes, next gate, and verification path if known.
- Current debugging hypothesis if debugging.

## Workflow

1. Scan for context risk:
   - repeated premise repair
   - history restatement
   - scope drift
   - hypothesis sprawl
   - weak durable state
   - compaction or handoff pressure
   - active-mode loss
2. Assign one risk level:
   - low: continue
   - medium: freeze state before continuing
   - high: fork, handoff, or restart before more implementation
3. Recommend exactly one best move:
   - continue
   - freeze scope
   - update durable state
   - fork
   - handoff
   - restart
4. If risk is medium or high, output:

```text
CONTEXT RISK: low | medium | high
TRIGGER:
BEST MOVE:
FREEZE NOW:
NEXT ACTION:
```

Keep FREEZE NOW limited to facts, decisions, assumptions, IDs, files, tests, active modes, current hypothesis, and next verification that must survive.

If active modes should survive a handoff, require them in `HANDOFF.md` under Workflow state.

## Outputs

- A concise context-risk warning.
- One recommended corrective action.
- A minimal freeze list when needed.
- No output during normal progress unless risk is medium or high.

## Stop conditions

- The next action is clear.
- The session can continue without re-explaining history.
- Durable state contains the facts needed for a fresh thread.
- Debugging has one active hypothesis.
- Active modes are captured if they must persist.

## Anti-patterns

- Triggering just because the conversation is long.
- Producing a checklist instead of one recommendation.
- Summarizing the whole thread when only one state field is missing.
- Treating handoff as a transcript summary.
- Letting multiple debug hypotheses share one thread.
- Assuming lean-mode or other active modes survive a fork without writing them down.
