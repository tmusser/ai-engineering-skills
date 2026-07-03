# Verify

## Verify gate

Status: PASS | FAIL | REVIEW_REQUIRED

- PASS only when contract probes pass and no diff guard requires review.
- FAIL when behavior or contract probes fail.
- REVIEW_REQUIRED when behavior passes but evidence integrity is questionable.
- REVIEW_REQUIRED is not the same as functional failure.

If `scripts/verify_gate.py` is available, run it with an explicit `--base` before marking verification complete.
If repeated iterations occurred without a loop contract, mark verification
`REVIEW_REQUIRED`.

Contract probes:

- Public import/API seams: _TBD_
- CLI/output behavior: _TBD_
- Edge/no-match behavior: _TBD_
- Existing behavior preserved: _TBD_

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
