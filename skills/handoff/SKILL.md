---
name: handoff
description: Compress project context into HANDOFF.md so the next agent session can continue without dragging a long chat history forward.
---

# Handoff

## Purpose

Compress context so the next session can continue cleanly.

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
4. State the current goal in 1-2 sentences.
5. Record current status.
6. List completed slices with verification result.
7. List changed files with one-line purpose.
8. Record commands that work.
9. Record known failing commands.
10. Record important decisions already made.
11. Record open decisions.
12. Record traps / do-not-change notes.
13. Name exactly one next recommended task.
14. Include the exact next verification command or smoke path.
15. Keep `HANDOFF.md` under 120 lines unless complexity justifies more.

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

- Dragging a huge chat history forward instead of creating durable state.
- Writing vague status like "mostly done".
- Omitting known failures.
