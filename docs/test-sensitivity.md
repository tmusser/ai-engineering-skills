# Test Sensitivity Fault-Injection Pass

`scripts/test_sensitivity.py` validates optional evidence that a targeted test can
actually detect the behavior it claims to protect.

This is not a mutation-testing framework. It is a narrow, opt-in test-integrity
tripwire for high-value deterministic tests.

## Declare the contract

In `SPEC.md`:

```text
## Test sensitivity gate

Test sensitivity requirement: REQUIRED

- Sensitivity ID: empty-export
  - Protected behavior: empty results return a header-only CSV
  - Test command: python -m pytest tests/test_export.py -k empty
  - Fault model: make empty results emit one body row
```

Use `NOT_APPLICABLE` when targeted fault injection would not buy meaningful
confidence for the slice. Legacy specs without the section remain compatible.

## Run the pass

For each declared Sensitivity ID:

1. Inject one narrow fault that should violate the protected behavior.
2. Prefer a disposable worktree, scratch copy, or exact reversible local edit.
3. Run the exact declared targeted test command.
4. Require a nonzero exit caused by the expected protected-behavior assertion or
   signal, not by syntax/import/setup failure.
5. Restore the implementation exactly.
6. Rerun the same targeted command and require exit code 0.

Do not inject faults into production, shared external state, or irreversible
data.

## Record evidence

In `VERIFY.md`:

```text
## Test sensitivity evidence

- Sensitivity ID: empty-export
  - Fault injected: empty branch emits one synthetic body row
  - Mutated command: python -m pytest tests/test_export.py -k empty
  - Mutated exit code: 1
  - Expected failure observed: yes
  - Failure evidence: assertion expected header-only output but observed one row
  - Restored exit code: 0
  - Restoration evidence: same targeted test passes after restoring implementation
```

The checker requires the mutated command to match the declared test command.

## Deterministic check

Direct:

```bash
python scripts/test_sensitivity.py --spec SPEC.md --verify VERIFY.md
```

Unified CLI:

```bash
python scripts/aes.py sensitivity --format json
```

Statuses:

- `PASS` — every required sensitivity probe records a killed fault for the
  expected reason and a clean restored rerun.
- `NOT_APPLICABLE` — the contract is absent or explicitly not applicable.
- `REVIEW_REQUIRED` — required evidence is missing, contradictory, survived the
  test, failed for the wrong reason, used a different command, or did not return
  to PASS after restoration.

Exit codes are 0 for `PASS` / `NOT_APPLICABLE` and 2 for `REVIEW_REQUIRED`.

## Verify-gate integration

When SPEC activates the contract, `verify_gate.py` prevents overall PASS until
the sensitivity evidence passes.

A surviving fault does not automatically mean the product implementation is
wrong. It means the test-integrity claim is not strong enough for an unqualified
verification PASS.

The review taxonomy distinguishes:

- `TEST_SENSITIVITY_SURVIVED` — the injected fault survived the targeted test or
  the test failed for a different reason;
- `TEST_SENSITIVITY_UNESTABLISHED` — required sensitivity evidence could not be
  established cleanly.

## Relationship to artifact consistency

The artifact cross-consistency linter composes this SPEC-to-VERIFY relationship
when active. It does not execute fault injection itself.

## Boundaries

The pass does not:

- generate mutations automatically;
- prove a test suite is sufficient;
- measure mutation score;
- prove the selected fault model is representative;
- authorize destructive testing or production-side fault injection;
- treat any nonzero test run as success.

## Claim boundary

A sensitivity `PASS` means the recorded targeted command failed under the
declared reversible fault for the expected protected-behavior reason and passed
again after restoration. It does not prove the test catches every realistic
regression.
