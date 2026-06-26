---
name: handoff
description: Compress project context into HANDOFF.md with workflow state, active modes, next gate, verification, current hypothesis, and resume packet for the next agent session.
---

# Handoff

## Purpose

Compress context into a launchpad for the next session. A handoff is not a transcript — it is durable state that lets a fresh agent continue safely without the full chat history.

## When to use

Use at the end of a session, before switching agents, or before pausing work.

## Inputs

- SPEC.md, PLAN.md, TODO.md, VERIFY.md
- Active modes, current phase, next gate
- Compatibility seams, invalid-if constraints, verify gate status, review-required items, next gate command when relevant
- Context risk level
- Active debugging hypothesis (if any)
- Branch, commit, dirty state
- Changed files, working/failing commands, unverified files
- Important decisions, open decisions, traps

## Workflow

1. Read current artifacts first.
2. Create or update HANDOFF.md starting with a **Resume Packet** block.
3. Record Workflow State (active modes, phase, loop, next gate, context risk, hypothesis).
4. Record continuation guardrails when relevant: compatibility seams preserved, invalid-if constraints, verify gate status, review-required items, next gate command.
5. State the current goal in 1-2 sentences.
6. List completed slices + verification results.
7. List changed files with one-line purpose (flag unverified).
8. Record working commands, known failing commands, important decisions, open decisions, and traps.
9. Name **exactly one** next recommended task + its verification command.
10. Keep under 120 lines unless complexity requires more.

**Resume Packet example (place near top):**

```text
RESUME PACKET

* Goal: ...
* Workflow State: lean-mode active, next gate=verify-contract, risk=low
* Branch: main, Commit: abc123, Dirty: no
* Next task: ...
* Verification: `python test_mini.py --slice=foo`
* Read first: HANDOFF.md, SPEC.md, PLAN.md, VERIFY.md (if present), then changed files below
```

## Outputs

- HANDOFF.md with Resume Packet + Workflow State
- Clear next task and verification path
- Continuation guardrails when relevant

## Success looks like

- A new agent can pick up the project from HANDOFF.md + core artifacts without rereading chat.
- All critical context (modes, risks, decisions, next gate) is in durable files.
- Exactly one next task is named.

## Stop conditions

- Next session can continue without full chat history.
- No important context lives only in memory.
- Next task and verification command are explicit.

## Anti-patterns

- Writing a chat transcript summary instead of state.
- Vague status ("mostly done").
- Omitting active modes, failing commands, or dirty state.
- Carrying multiple debug hypotheses forward.
- No explicit next gate or verification.
