---
name: verify-contract
description: Record clear evidence that a task works, including commands, results, remaining risks, scope adherence, and whether the implementation stayed under the spec ceiling.
---

# Verify Contract

## Purpose

Prove the task actually works and leave durable evidence.

Verification also checks that the implementation did not exceed the behavioral contract or frozen write boundary merely because the extra work looked reasonable.

## When to use

After implementation, tests, bug fixes, data runs, or smoke checks.

## Inputs

- Task name
- `SPEC.md` acceptance criteria, non-goals, constraints, and invalid-if rules
- Optional persisted `SCOPE.md` plus its frozen Git base
- Commands run or to run
- Changed files
- Evidence to record
- Known risks or untested areas

## Workflow

1. Update VERIFY.md with date + task name.
2. Record commands run as short evidence entries with command, exit code, relevant
   output, interpretation, acceptance criterion covered, and remaining uncertainty.
   Keep each entry concise and auditable.
3. When `SCOPE.md` and `scripts/scope_gate.py` are available, run:

   ```bash
   python scripts/scope_gate.py --base <frozen-base>
   ```

   Record its status and relevant violations or review triggers. A scope-gate `FAIL` prevents PASS. `REVIEW_REQUIRED` also prevents PASS until the named review is resolved.
4. If `scripts/verify_gate.py` is available, run it before marking verification complete.
   If repeated iterations were used, check for a loop contract, budget, ledger,
   revert rule, and stop condition before calling the work done.
5. List changed files.
6. Run the spec ceiling check against the implemented behavior and diff.
7. Note working directory / environment assumptions if relevant.
8. Link artifacts/screenshots if relevant (supporting evidence only; automated checks preferred).
9. Note what was **not** tested and remaining risks.
10. Name the next safest task.

## Verify gate

Status: PASS | FAIL | REVIEW_REQUIRED

- PASS only when contract probes pass, the scope gate passes when a persisted scope exists, no diff guard requires review, and no spec ceiling violation is present.
- FAIL when behavior or contract probes fail, the scope gate fails, or an explicit non-goal / invalid-if rule was violated.
- REVIEW_REQUIRED when behavior passes but evidence integrity is questionable, the scope gate requires review, or plausible extra behavior exceeds the written acceptance criteria and intent is ambiguous.
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

Scope adherence:

- Scope gate: PASS | FAIL | REVIEW_REQUIRED | NOT_APPLICABLE
- Out-of-scope writes: none | describe
- Read-only / forbidden paths touched: none | describe
- Review triggers resolved: yes/no/not applicable
- Scope artifact widened after implementation began: no | describe

Any scope-gate `FAIL` prevents PASS. Unresolved scope-gate `REVIEW_REQUIRED` also prevents PASS.

Spec ceiling:

- Unspecified user-visible / API / schema behavior added: yes/no
- Explicit non-goal implemented: yes/no
- Adjacent refactor or cleanup beyond necessary support: yes/no
- Necessary spec expansion discovered but not written down first: yes/no

Any `yes` above prevents PASS. Use FAIL for a clear contract violation; use
REVIEW_REQUIRED when the extra behavior may be reasonable but was not authorized by the
written spec.

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
- Scope-gate status when a persisted scope exists
- Pass/fail summary + automated/manual/inferred status
- Spec ceiling result
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

Scope gate: PASS — all changed files remained within SCOPE.md
Spec ceiling: PASS — no unspecified behavior or adjacent cleanup added
Changed: src/export.py, tests/export_test.py
Not tested: large dataset edge case
Remaining risks: large dataset edge case (monitor in prod)
Next: Add scheduling wrapper
```

## Stop conditions

- Evidence is recorded clearly.
- Persisted scope was checked against the live diff.
- Spec ceiling was checked against the actual diff and behavior.
- Scope or verification failures trigger diagnosis; do not mark them as passed.

## Anti-patterns

- "Looks good" without evidence.
- Hiding failed commands.
- Marking PASS after a scope-gate failure or unresolved review trigger.
- Rewriting `SCOPE.md` after implementation to retroactively authorize the diff.
- Calling extra behavior harmless because tests still pass.
- Using screenshots as primary evidence for non-visual tasks.
