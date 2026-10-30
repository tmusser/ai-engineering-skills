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
- `SPEC.md` acceptance criteria, non-goals, constraints, invalid-if rules, optional implementation diff budget, and optional test-sensitivity contract
- Optional persisted `SCOPE.md` plus its frozen Git base
- Commands run or to run
- Changed files
- Evidence to record
- Known risks or untested areas
- Optional operator profile `Verification depth`

## Workflow

1. Update VERIFY.md with date + task name.
2. Record commands run as short evidence entries with command, exit code, relevant
   output, interpretation, acceptance criterion covered, and remaining uncertainty.
   Keep each entry concise and auditable.
3. For new verification records, maintain a machine-readable `Structured
   verification evidence` JSON block alongside the human-readable evidence. Use
   schema version 1 and one record per meaningful check with:
   `check`, `command`, `exit_code`, `evidence_source`, `status`,
   `evidence`, plus at least one of `recorded_at` or `commit`. Use `null`
   for command fields when evidence is manual or artifact-backed. Keep evidence
   short; do not copy raw logs or secrets into the JSON block. When SPEC
   explicitly labels every acceptance criterion `AC-1`, `AC-2`, etc., set
   the matching single `acceptance_criterion` ID in each supporting check.
   The optional PR coverage summary reports gaps; linking evidence does not
   prove semantic correctness.
4. When `SCOPE.md` and `scripts/scope_gate.py` are available, run:

   ```bash
   python scripts/scope_gate.py --base <frozen-base>
   ```

   Record its status and relevant violations or review triggers. A scope-gate `FAIL` prevents PASS. `REVIEW_REQUIRED` also prevents PASS until the named review is resolved.
5. If SPEC.md marks the compatibility probe gate `REQUIRED`, rerun every named
   probe after implementation and record matching post-change evidence under the
   same Probe ID. Missing or mismatched probe evidence requires review; an
   explicit failed post-change probe prevents PASS.
6. If SPEC.md marks `Test sensitivity requirement: REQUIRED`, perform the narrow fault-injection pass from `test-mini`: run the exact declared targeted test against one reversible fault, confirm the expected protected-behavior failure, restore the implementation, and prove the same test returns to PASS. Record the matching Sensitivity ID evidence in VERIFY.md. A surviving fault or wrong failure mode requires review; it is not automatically a functional failure.
7. If `scripts/verify_gate.py` is available, run it before marking verification complete. When SPEC.md declares an `ENFORCED` implementation diff budget, inspect the deterministic `diff-budget` result before PASS. Budget overruns are `REVIEW_REQUIRED`, not automatic functional failures. If repeated iterations were used, check for a loop contract, budget, ledger, revert rule, and stop condition before calling the work done.
8. When multiple durable workflow artifacts are present and `scripts/check_artifact_consistency.py` is available, run the cross-consistency linter before final PASS. It composes existing lineage, acceptance-coverage, and compatibility contracts plus SPEC↔SCOPE, SCOPE↔VERIFY, and VERIFY↔HANDOFF consistency seams. Do not invoke it merely to require absent optional artifacts.
9. Before recording `PASS`, add or refresh the verification freshness anchors and
   stamp the repository snapshot:

   ```text
   ## Verification freshness

   - Snapshot commit: `_TBD_`
   - Workspace fingerprint: `_TBD_`
   ```

   ```bash
   python skills/verify-contract/scripts/verification_freshness.py stamp
   ```

   The fingerprint excludes `VERIFY.md` itself, so recording or committing the
   verification artifact does not immediately invalidate it. Any later source,
   test, fixture, dependency, or other repository-state change makes the stamped
   evidence stale until affected verification is rerun and stamped again.
10. List changed files.
11. Run the spec ceiling check against the implemented behavior and diff.
12. Note working directory / environment assumptions if relevant.
13. Link artifacts/screenshots if relevant (supporting evidence only; automated checks preferred).
14. Note what was **not** tested and remaining risks.
15. If an operator profile provides `Verification depth`, use it only to size
    optional proof beyond the required contract: `targeted` stops at required
    evidence, `standard` adds cheap relevant regression proof, and `expanded`
    allows additional adjacent high-value checks when low-cost. Required gates,
    compatibility probes, and named risks remain mandatory in every mode.
16. Name the next safest task.

## Verify gate

Status: PASS | FAIL | REVIEW_REQUIRED

- PASS only when contract probes pass, structured verification evidence is valid when present, every REQUIRED compatibility probe has matching post-change PASS evidence, every REQUIRED test-sensitivity probe has killed-and-restored evidence, the scope gate passes when a persisted scope exists, any enforced implementation diff budget passes, active durable artifacts are cross-consistent when that linter applies, no diff guard requires review, and no spec ceiling violation is present.
- FAIL when behavior or contract probes fail, a required post-change compatibility probe fails, the scope gate fails, or an explicit non-goal / invalid-if rule was violated.
- REVIEW_REQUIRED when behavior passes but evidence integrity is questionable, required test-sensitivity evidence is missing or a declared fault survives the targeted test, stamped verification is stale, the scope gate requires review, active durable artifacts contradict one another without a clear functional failure, an enforced implementation diff budget is exceeded or unmeasurable, or plausible extra behavior exceeds the written acceptance criteria and intent is ambiguous.
- REVIEW_REQUIRED is not the same as functional failure.
- When the deterministic verify gate supplies review reason codes, preserve them as routing metadata. Codes explain why review is required; they do not change top-level severity.
- If repeated iterations occurred without a loop contract, use REVIEW_REQUIRED.
- If loop budget, ledger, revert rule, or stop condition was violated, use REVIEW_REQUIRED
  or FAIL depending on whether the behavior contract failed.
- Do not treat loop activity as success merely because the final output looks plausible.

Review-required reason taxonomy:

When `scripts/verify_gate.py` returns `REVIEW_REQUIRED`, it also emits stable
machine-readable `review_reasons` with `code`, `category`, and `details`.
Keep the existing human-readable reason text. Use the code for routing, not as a
replacement status.

Common codes include:

- `SPEC_MISSING` / `SPEC_INCOMPLETE`
- `VERIFY_REVIEW_REQUESTED`
- `STRUCTURED_EVIDENCE_INVALID`
- `COMPATIBILITY_UNCERTAIN`
- `VERIFICATION_STALE` / `VERIFICATION_FRESHNESS_UNESTABLISHED`
- `DIFF_BUDGET_INCOMPLETE` / `DIFF_BUDGET_UNMEASURABLE` /
  `DIFF_BUDGET_EXCEEDED`
- `PROTECTED_PATH_CHANGED`
- `TESTS_CHANGED`
- `FIXTURE_DATA_CHANGED`
- `DEPENDENCIES_CHANGED`
- `TEST_SENSITIVITY_UNESTABLISHED` / `TEST_SENSITIVITY_SURVIVED`
- `UNCLASSIFIED_REVIEW` for a review state not yet assigned a dedicated code

Do not invent a different severity from a reason code. A `TESTS_CHANGED` review
is still `REVIEW_REQUIRED`; a failed compatibility probe remains `FAIL`.

Structured verification evidence:

- Schema version: `1`
- Required fields per check: `check`, `command`, `exit_code`,
  `evidence_source`, `status`, `evidence`
- Provenance: at least one of `recorded_at` or `commit`
- Evidence sources: `command | artifact | manual | inferred`
- Status: `PASS | FAIL | REVIEW_REQUIRED`

Once the section exists, malformed JSON, duplicate check IDs, unknown fields,
placeholder evidence, missing provenance, or a PASS command with a nonzero exit
code prevents PASS. An explicit structured `FAIL` is a verification failure.
Legacy artifacts without the section remain compatible.

Contract probes:

- Public import/API seams:
- CLI/output behavior:
- Config/default behavior:
- Edge/no-match behavior:
- Existing behavior preserved:

Compatibility probe evidence:

When SPEC.md says `Compatibility probe requirement: REQUIRED`, record one block
for every baseline Probe ID:

- Probe ID: _TBD_
  - Post-change command: _TBD_
  - Result: PASS | FAIL | REVIEW_REQUIRED
  - Evidence: _TBD_

The Probe ID must match the pre-change baseline in SPEC.md. Missing, duplicate,
undeclared, or incomplete probe evidence prevents PASS. An explicit `FAIL`
means the compatibility seam regressed. Do not rewrite the baseline after implementation to make a changed behavior look compatible.

Test sensitivity evidence:

When SPEC says `Test sensitivity requirement: REQUIRED`, VERIFY.md must carry
one matching Sensitivity ID block for each declared probe. PASS requires:

- the exact declared `Test command` is rerun after fault injection;
- the mutated run exits nonzero;
- the expected protected-behavior failure is explicitly observed;
- concise failure evidence is recorded;
- the fault is fully restored;
- the same targeted test returns exit code 0 after restoration.

A generic syntax/import/setup crash does not count as killing the fault. A fault
that survives, fails for the wrong reason, or cannot be restored cleanly remains
`REVIEW_REQUIRED`. This check validates evidence; it does not execute mutation
testing automatically.

Scope adherence:

- Scope gate: PASS | FAIL | REVIEW_REQUIRED | NOT_APPLICABLE
- Out-of-scope writes: none | describe
- Read-only / forbidden paths touched: none | describe
- Review triggers resolved: yes/no/not applicable
- Scope artifact widened after implementation began: no | describe

Any scope-gate `FAIL` prevents PASS. Unresolved scope-gate `REVIEW_REQUIRED` also prevents PASS.

Operator-profile `Verification depth` never lowers this floor. It controls only
optional proof beyond the task contract and deterministic gates.

Spec ceiling:

- Unspecified user-visible / API / schema behavior added: yes/no
- Explicit non-goal implemented: yes/no
- Adjacent refactor or cleanup beyond necessary support: yes/no
- Necessary spec expansion discovered but not written down first: yes/no

Any `yes` above prevents PASS. Use FAIL for a clear contract violation; use
REVIEW_REQUIRED when the extra behavior may be reasonable but was not authorized by the
written spec.

Implementation diff budget:

- Requirement: `ENFORCED | NOT_APPLICABLE`
- Max changed files: from SPEC.md
- Max added lines: from SPEC.md
- Workflow-control artifacts do not consume the implementation budget.
- Exceeding the budget requires review before PASS; it does not by itself prove a
  functional or contract failure.
- Do not enlarge the recorded budget after implementation merely to make the
  gate green.

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

Verification freshness:

- Snapshot commit: `_TBD_`
- Workspace fingerprint: `_TBD_`

A stamped freshness mismatch prevents PASS. Rerun the affected verification,
update `VERIFY.md`, and stamp the new repository state rather than carrying
forward old evidence.

Review required because:

- _TBD_

## Outputs

- VERIFY.md entry with human-readable and machine-readable evidence
- Verify gate status
- Deterministic review reason codes when the verify gate requires review
- Matched compatibility probe evidence when the spec requires it
- Test-sensitivity fault-injection evidence when the spec requires it
- Scope-gate status when a persisted scope exists
- Diff-budget status when SPEC.md opts into enforcement
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
- Adding machine-readable fields that contradict the human-readable result.
- Copying full logs, secrets, or noisy tool output into structured evidence.
- Hiding failed commands.
- Marking PASS after a scope-gate failure or unresolved review trigger.
- Editing code after verification and leaving the old PASS evidence stamped as current.
- Recording compatibility expectations only after implementation, when the baseline can no longer constrain the change.
- Rewriting `SCOPE.md` after implementation to retroactively authorize the diff.
- Calling extra behavior harmless because tests still pass.
- Using screenshots as primary evidence for non-visual tasks.
- Counting an unrelated test crash as a killed fault.
- Leaving a deliberate fault in the working tree after a sensitivity check.
