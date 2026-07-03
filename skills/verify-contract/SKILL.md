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
2. Record commands run as short evidence entries with command, exit code, relevant
   output, interpretation, acceptance criterion covered, and remaining uncertainty.
   Keep each entry concise and auditable. If `scripts/verify_gate.py` is available,
   run it before marking verification complete.
   If repeated iterations were used, check for a loop contract, budget, ledger,
   revert rule, and stop condition before calling the work done.
3. List changed files.
4. Note working directory / environment assumptions if relevant.
5. Link artifacts/screenshots if relevant (supporting evidence only; automated checks preferred).
6. Note what was **not** tested and remaining risks.
7. Name the next safest task.

## Verify gate

Status: PASS | FAIL | REVIEW_REQUIRED

- PASS only when contract probes pass and no diff guard requires review.
- FAIL when behavior or contract probes fail.
- REVIEW_REQUIRED when behavior passes but evidence integrity is questionable.
- REVIEW_REQUIRED is not the same as functional failure.
- If repeated iterations occurred without a loop contract, use REVIEW_REQUIRED.
- If loop budget, ledger, revert rule, or stop condition was violated, use REVIEW_REQUIRED
  or FAIL depending on whether the behavior contract failed.
- Do not treat loop activity as success merely because the final output looks plausible.

Contract probes:

- Public import/API seams:
- CLI/output behavior:
- Edge/no-match behavior:
- Existing behavior preserved:

Diff guards:

- Protected paths touched: yes/no
- Tests changed: yes/no
- Fixture/data changed: yes/no
- Dependencies changed: yes/no

Credential boundary check:

- Confirm `.env` or local secret files were not modified unless they were explicitly in scope.
- Confirm no API keys, tokens, cookies, passwords, or private URLs were added.
- If a secret is needed, document only the environment variable name. Environment variable names are okay; raw secret values are not.
- Run a repo secret scan if one already exists and is easy to invoke.
- Mark `REVIEW_REQUIRED` if credential exposure is uncertain.

This is a lightweight workflow check, not a secret scanner or a replacement for
permissions, secret scanning, or runtime controls.

Review required because:

- _TBD_

## Outputs

- VERIFY.md entry with evidence
- Verify gate status
- Pass/fail summary + automated/manual/inferred status
- Remaining / untested risks
- Next safest task

## Success looks like

**Good VERIFY.md entry:**

```text
2026-06-09 - Implement user export
Environment: Python 3.11, clean venv

Command: ./run_export_test.sh
Exit code: 0
Relevant output: export summary matched fixture
Interpretation: passed
Acceptance criterion covered: user export happy path
Remaining uncertainty: large dataset edge case

Command: python -m pytest tests/export_test.py
Exit code: 0
Relevant output: 12 passed
Interpretation: passed
Acceptance criterion covered: test coverage for export behavior
Remaining uncertainty: none known

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
