---
name: handoff
description: Compress project context into HANDOFF.md for the next agent session.
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
- Changed files from the session
- Working and failing commands
- Important decisions
- Open decisions
- Traps / do-not-change notes

## Workflow

1. Read existing artifacts before writing the handoff.
2. Avoid summarizing the whole conversation.
3. Prefer file pointers over copied code.
4. Include a short "For the next agent" block near the top.
5. In that block, instruct the next agent to read `SPEC.md`, `PLAN.md`, `TODO.md`, `VERIFY.md`, and the changed files listed in the handoff.
6. In that block, instruct the next agent to confirm the current phase and goal, next recommended task, and verification command or smoke path.
7. In that block, instruct the next agent to state assumptions before proceeding.
8. State the current goal in 1-2 sentences.
9. Record current status.
10. List completed slices with verification result.
11. List changed files with one-line purpose.
12. Record commands that work.
13. Record known failing commands.
14. Record important decisions already made.
15. Record open decisions.
16. Record traps / do-not-change notes.
17. Name exactly one next recommended task.
18. Include the exact next verification command or smoke path.
19. Keep `HANDOFF.md` under 120 lines unless complexity justifies more.

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
