# Handoff

## Purpose

Compress context so the next session can continue cleanly.

## When to use

Use at the end of a session, before changing agents, or before pausing a project.

## Inputs

- Project goal
- Current status
- Completed tasks
- Changed files
- Working and failing commands
- Open decisions

## Workflow

1. Update `HANDOFF.md`.
2. State the project goal.
3. Record current status.
4. List completed slices.
5. List changed files.
6. Record commands that work.
7. Record known failing commands.
8. Capture open decisions.
9. Add traps or do-not-change notes.
10. Name the next recommended task.

## Outputs

- `HANDOFF.md`
- Compressed session context
- Next recommended task

## Stop conditions

- A new session can continue without reading the full chat.
- Important context is still only in memory or chat.

## Anti-patterns

- Dragging a huge chat history forward instead of creating durable state.
- Writing vague status like "mostly done".
- Omitting known failures.
