---
name: bug-capture
description: Preserve discovered bugs in BUGS.md with reproduction steps, expected behavior, affected files, hypothesis, status, and verification.
---

# Bug Capture

## Purpose

Preserve discovered bugs as durable artifacts.

## When to use

Use when a bug is found, whether or not it is fixed in the current session.

## Inputs

- Observed behavior
- Expected behavior
- Reproduction steps
- Affected files
- Verification command

## Workflow

1. Create or update `BUGS.md`.
2. Add a bug title.
3. Record observed and expected behavior.
4. Write reproduction steps.
5. List affected files.
6. Add hypothesis and status.
7. Record verification command.
8. Add resolution if fixed.

## Outputs

- `BUGS.md` entry with:
- Bug title
- Observed behavior
- Expected behavior
- Reproduction steps
- Affected files
- Hypothesis
- Status
- Verification command
- Resolution if fixed

## Stop conditions

- The bug is captured well enough for another session to reproduce.
- The issue is not a bug and should become a decision or task instead.

## Anti-patterns

- Leaving bug knowledge trapped in chat history.
- Recording "broken" without reproduction steps.
- Closing a bug without verification evidence.
