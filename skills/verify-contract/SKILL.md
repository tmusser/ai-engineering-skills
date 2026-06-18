---
name: verify-contract
description: Record clear evidence that a task works, including commands, results, and remaining risks.
---

# Verify Contract

## Purpose

Prove the task actually works and leave durable evidence.

## When to use

After implementation, tests, bug fixes, data runs, or smoke checks.

## Inputs

- Task name
- Commands run or to run
- Changed files
- Evidence to record
- Known risks or untested areas

## Workflow

1. Update VERIFY.md with date + task name.
2. Record commands run + pass/fail output.
3. List changed files.
4. Note working directory / environment assumptions if relevant.
5. Link artifacts/screenshots if relevant (supporting evidence only; automated checks preferred).
6. Note what was **not** tested and remaining risks.
7. Name the next safest task.

## Outputs

- VERIFY.md entry with evidence
- Pass/fail summary + automated/manual/inferred status
- Remaining / untested risks
- Next safest task

## Success looks like

**Good VERIFY.md entry:**

```text
2026-06-09 - Implement user export
Environment: Python 3.11, clean venv

Commands:
./run_export_test.sh → PASSED (output attached)
python -m pytest tests/export_test.py → PASSED (automated)

Changed: src/export.py, tests/export_test.py
Not tested: large dataset edge case
Remaining risks: large dataset edge case (monitor in prod)
Next: Add scheduling wrapper
```

## Stop conditions

- Evidence is recorded clearly.
- Failures trigger diagnosis (do not mark as passed).

## Anti-patterns

- "Looks good" without evidence.
- Hiding failed commands.
- Using screenshots as primary evidence for non-visual tasks.
