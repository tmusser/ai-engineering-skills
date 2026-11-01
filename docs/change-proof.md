# Baseline → Change → Proof

Use the optional change-proof contract when a slice is supposed to change an
observable behavior and the strongest evidence is a stable before/after probe.

This fills a different role from compatibility and test sensitivity:

- compatibility probe: prove a named seam stayed the same;
- change proof: prove an intended behavior changed as specified;
- test sensitivity: prove a targeted test can detect a deliberate break.

## Contract

In `SPEC.md`, capture the before state before implementation:

```text
## Change proof gate

Change proof requirement: REQUIRED

- Change ID: export-empty
  - Baseline commit: abc1234
  - Baseline command: python -m pytest tests/test_export.py -k empty
  - Baseline exit code: 1
  - Baseline evidence: empty-export assertion fails
  - Expected delta: targeted test changes from failing to passing
```

The baseline command should be a stable probe that can run unchanged before and
after the implementation. The baseline commit should be the frozen verification
base.

Once implementation starts, the baseline is immutable. If it was not captured
correctly, stop and review rather than reconstructing a convenient before state
from memory or from the completed patch.

## Implement the bounded change

Build only the accepted slice. The change-proof contract does not expand scope
or authorize adjacent behavior.

If other behavior must remain unchanged, use compatibility probes alongside the
change proof rather than overloading the expected delta with preserved seams.

## Record post-change proof

In `VERIFY.md`:

```text
## Change proof evidence

- Change ID: export-empty
  - Proof command: python -m pytest tests/test_export.py -k empty
  - Proof exit code: 0
  - Delta result: PASS
  - Proof evidence: targeted empty-export assertion now passes
```

The proof command must match the baseline command exactly.

Status semantics:

- `PASS` — every required Change ID has matching proof, exit code 0, and an
  explicit PASS delta result;
- `FAIL` — the post-change evidence explicitly says the intended delta was not
  proven;
- `REVIEW_REQUIRED` — baseline/proof evidence is missing, commands do not match,
  the baseline commit does not match the verification base, or PASS evidence is
  internally inconsistent.

## Deterministic checker

Direct:

```bash
python scripts/change_proof.py --base origin/main --format json
```

Unified CLI:

```bash
python scripts/aes.py change-proof --base origin/main --format json
```

`verify_gate.py` runs the same contract against its required `--base` when the
SPEC activates change proof.

## Example: bug fix

A regression test currently fails:

```text
Baseline exit code: 1
Expected delta: failing regression test becomes passing
```

After the fix, rerun the exact same test:

```text
Proof exit code: 0
Delta result: PASS
```

That is stronger than recording only the final green test because it preserves
evidence that the probe actually distinguished the old behavior from the new.

## When not to use it

Use `NOT_APPLICABLE` when:

- the task is mechanical and no meaningful behavioral baseline exists;
- the intended behavior is purely additive but no stable before/after probe can
  be defined cheaply;
- compatibility proof already captures the relevant risk because behavior is
  supposed to stay unchanged;
- the comparison would rely only on subjective prose with no stable probe.

Do not add a change proof merely to increase ceremony.

## Claim boundary

A change-proof PASS establishes that the declared stable probe moved from the
recorded baseline state to a post-change PASS consistent with the written
expected delta. It does not prove all behavior changed correctly, that every
regression risk was covered, or that unrelated compatibility seams were
preserved. Matching the baseline commit anchors the claimed before state to the
verification base, but it cannot prove when the observation was actually
recorded. Use repository history or stronger external provenance when capture
timing itself matters.
