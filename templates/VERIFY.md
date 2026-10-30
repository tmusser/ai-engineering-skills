# Verify

## Contract identity (optional)

Contract ID: _TBD_

_Omit this section when SPEC.md has no active contract ID. Otherwise copy the active SPEC contract ID exactly._

## Verify gate

Status: PASS | FAIL | REVIEW_REQUIRED

- PASS only when contract probes pass and no diff guard requires review.
- FAIL when behavior or contract probes fail.
- REVIEW_REQUIRED when behavior passes but evidence integrity is questionable.
- REVIEW_REQUIRED is not the same as functional failure.

When `scripts/verify_gate.py` returns review reason codes, keep them with the review evidence. Codes classify the reason for review; they do not change `PASS | FAIL | REVIEW_REQUIRED` severity. Do not invent a code to override the gate. See `docs/review-required-taxonomy.md`.

If `scripts/verify_gate.py` is available, run it with an explicit `--base` before marking verification complete.
If repeated iterations occurred without a loop contract, mark verification
`REVIEW_REQUIRED`.

Contract probes:

- Public import/API seams: _TBD_
- CLI/output behavior: _TBD_
- Config/default behavior: _TBD_
- Edge/no-match behavior: _TBD_
- Existing behavior preserved: _TBD_

Compatibility probe evidence:

_Required only when SPEC.md says `Compatibility probe requirement: REQUIRED`.
Repeat this block for every baseline Probe ID._

- Probe ID: _TBD_
  - Post-change command: _TBD_
  - Result: PASS | FAIL | REVIEW_REQUIRED
  - Evidence: _TBD_

Missing, duplicate, undeclared, or incomplete required probe evidence prevents
PASS. An explicit failed post-change probe means the compatibility seam regressed.

Test sensitivity evidence:

_Required only when SPEC says `Test sensitivity requirement: REQUIRED`. Repeat
this block for every declared Sensitivity ID._

- Sensitivity ID: _TBD_
  - Fault injected: _TBD_
  - Mutated command: _TBD_
  - Mutated exit code: _TBD_
  - Expected failure observed: yes/no
  - Failure evidence: _TBD_
  - Restored exit code: _TBD_
  - Restoration evidence: _TBD_

A killed fault requires the exact declared targeted command to exit nonzero for
the expected protected-behavior failure, followed by exit 0 after restoration.
A surviving fault, wrong failure mode, missing restoration proof, or mismatched
command prevents PASS and requires review.
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

Deterministic review reason codes (when emitted by verify gate):

- _TBD_

## Loop readiness

Required only if repeated agent iterations occurred or are planned.

- Loop contract present: yes/no/n/a
- Iterations run: _TBD_
- Feedback signal used: _TBD_
- Budget respected: yes/no/n/a
- Revert rule followed: yes/no/n/a
- Ledger updated: yes/no/n/a
- Stop condition met: yes/no/n/a
- Review required because: _TBD_

## Verify gate evidence

- Protected paths declared: _TBD_
- Forbidden paths declared: _TBD_
- Compatibility seams: _TBD_
- Invalid-if constraints: _TBD_

## Structured verification evidence

_New verification runs should keep one machine-readable record per meaningful
check. Legacy VERIFY.md files without this section remain valid. Once this section
exists, malformed or contradictory records require review._

```json
{
  "schema_version": 1,
  "checks": [
    {
      "check": "_TBD_",
      "command": null,
      "exit_code": null,
      "evidence_source": "command",
      "status": "PASS",
      "evidence": "_TBD_",
      "recorded_at": "_TBD_",
      "commit": null,
      "acceptance_criterion": "_TBD_",
      "remaining_uncertainty": "_TBD_"
    }
  ]
}
```

Required per check: `check`, `command`, `exit_code`, `evidence_source`,
`status`, and `evidence`, plus at least one provenance anchor:
`recorded_at` or `commit`. Use `null` for `command` and `exit_code` when
the evidence source is not a command. When the SPEC uses explicit `AC-1`,
`AC-2` criterion IDs, record a single exact ID in `acceptance_criterion`
for every linked check. The optional coverage report identifies missing links;
a link is not a correctness claim.

## Command evidence

Use a short, auditable record for each meaningful command:

- Command: _TBD_
- Exit code: _TBD_
- Relevant output: _TBD_
- Interpretation: _TBD_
- Acceptance criterion covered: _TBD_
- Remaining uncertainty: _TBD_

## Build note

- Selected slice: _TBD_
- Files touched: _TBD_
- Why each file was touched: _TBD_
- Compatibility seams preserved: _TBD_
- Tests changed: yes/no
- Verification run: _TBD_
- Stop reason: _TBD_

## Verification

- Date: _TBD_
- Task: _TBD_
- Commands run: _TBD_
- Result: _TBD_
- Changed files: _TBD_
- Screenshots/artifacts: _TBD_
- Remaining unverified risks: _TBD_
- Next safest task: _TBD_
