---
name: handoff
description: Compress project context into HANDOFF.md with workflow state, active modes, next gate, verification, current hypothesis, fresh context, and fork guidance for the next agent session.
---

# Handoff

## Purpose

Compress context for the next session.

A handoff is not a transcript. It is a launchpad for the next safe action.

## When to use

Use at the end of a session, before changing agents, or before pausing a project.

## Inputs

- `SPEC.md`
- `PLAN.md`
- `TODO.md`
- `VERIFY.md`
- Active modes
- Current phase
- Current workflow loop
- Next gate
- Context risk
- Active debugging hypothesis
- Resume command for the next session
- Changed files from the session
- Working and failing commands
- Important decisions
- Open decisions
- Traps / do-not-change notes

## Workflow

1. Read existing artifacts before writing the handoff.
2. Fill `Workflow state` before project details.
3. Record active modes that must survive a fresh thread, such as `lean-mode` or `context-check passive`.
4. Record the current phase, loop, next gate, context risk, and active hypothesis if debugging.
5. Write a `Resume command` that a fresh agent can follow without reading the full transcript.
6. Avoid summarizing the whole conversation.
7. Prefer file pointers over copied code.
8. Include a short `Resume packet` block near the top.
9. In that block, instruct the next agent to read `SPEC.md`, `PLAN.md`, `TODO.md`, `VERIFY.md`, and the changed files listed in the handoff.
10. In that block, require a `Workflow state` section with active modes, current phase, current loop, next gate, context risk, and active hypothesis.
11. In that block, instruct the next agent to confirm the current phase and goal, next recommended task, and verification command or smoke path.
12. In that block, instruct the next agent to state assumptions before proceeding.
13. State the current goal in 1-2 sentences.
14. Record current status.
15. List completed slices with verification result.
16. List changed files with one-line purpose.
17. Record commands that work.
18. Record known failing commands.
19. Record important decisions already made.
20. Record open decisions.
21. Record traps / do-not-change notes.
22. Name exactly one next recommended task.
23. Include the exact next verification command or smoke path.
24. Keep `HANDOFF.md` under 120 lines unless complexity justifies more.

## Outputs

- `HANDOFF.md`
- Compressed session context
- Next recommended task

## Stop conditions

- A new session can continue without reading the full chat.
- No important context remains only in memory or chat.
- The next task and its verification command are explicit.
- The handoff is brief enough to avoid becoming a context dump.

## Anti-patterns

- Dragging a huge chat history forward instead of creating state.
- Writing vague status like "mostly done".
- Omitting known failures.
- Assuming active modes survive without writing them into `HANDOFF.md`.
- Writing a transcript summary instead of a resume packet.
- Omitting the next gate or verification command.
- Carrying multiple debug hypotheses into the next thread.
