---
name: verify-contract
description: Record proof that a task works by capturing commands, pass/fail results, changed files, artifacts, risks, and the next safest task.
---

# Verify Contract

## Purpose

Record proof that a task actually works.

## When to use

Use after implementation, testing, bug fixes, data runs, screenshots, or manual smoke checks.

## Inputs

- Task name
- Changed files
- Commands run
- Artifacts or screenshots
- Remaining risks

## Workflow

1. Update `VERIFY.md`.
2. Record date and task.
3. Record commands run with pass/fail result.
4. List changed files.
5. Link screenshots or artifacts if applicable.
6. Record remaining unverified risks.
7. Name the next safest task.

## Outputs

- `VERIFY.md` entry with evidence
- Pass/fail summary
- Remaining risks
- Next safest task

## Stop conditions

- Evidence is recorded clearly.
- Verification failed and diagnosis should start.

## Anti-patterns

- Saying "looks good" without command output or evidence.
- Recording only successful commands while hiding failed ones.
- Treating screenshots as a substitute for data checks.
