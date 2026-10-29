# Artifact Cross-Consistency Linter

`scripts/check_artifact_consistency.py` checks whether durable workflow artifacts
agree with one another.

It is deliberately narrower than the repository's individual gates. A document
can be internally valid and still contradict another artifact. This linter looks
for those cross-artifact contradictions without rerunning implementation tests or
the live Git diff.

## Recommended command

Run from the task repository root:

```bash
python scripts/check_artifact_consistency.py
```

Machine-readable output:

```bash
python scripts/check_artifact_consistency.py --format json
```

The unified CLI exposes the same command:

```bash
python scripts/aes.py consistency --format json
```

Custom artifact locations are supported:

```bash
python scripts/check_artifact_consistency.py \
  --spec state/SPEC.md \
  --plan state/PLAN.md \
  --scope state/SCOPE.md \
  --verify state/VERIFY.md \
  --handoff state/HANDOFF.md
```

## What it composes

The linter reuses existing deterministic checks instead of maintaining parallel
interpretations:

- optional contract lineage across `SPEC.md`, `PLAN.md`, `VERIFY.md`, and
  `HANDOFF.md`;
- optional AC-ID acceptance-to-evidence coverage from `SPEC.md` to `VERIFY.md`;
- optional compatibility-probe baseline/evidence matching from `SPEC.md` to
  `VERIFY.md`.

Those tools remain the source of truth for their own contracts.

## Additional cross-artifact seams

### SPEC ↔ SCOPE diff budget

When SPEC enforces a max changed-file implementation budget and SCOPE also
records a hard `Max files changed` cap, the scope cap should not exceed the
accepted SPEC budget.

```text
SPEC max changed files: 3
SCOPE max files changed: 5
=> REVIEW_REQUIRED
```

This is review rather than failure because the larger hard scope may be
intentional after a legitimate renegotiation, but the artifacts no longer prove
that history.

If SCOPE omits a hard file cap, this seam is `NOT_APPLICABLE`; the SPEC
diff-budget gate still owns its own enforcement.

### SCOPE ↔ VERIFY applicability

If `SCOPE.md` exists, `VERIFY.md` should record a concrete scope-gate status.

A persisted scope plus:

```text
Scope gate: NOT_APPLICABLE
```

requires review.

Likewise, VERIFY cannot claim a scope-gate result when no SCOPE artifact exists.

The linter does not rerun `scope_gate.py`; it checks only whether the artifact
claims agree about whether a scope contract was active.

### VERIFY ↔ HANDOFF continuation state

When HANDOFF exists, its recorded `Verify gate status` must match the current
status in VERIFY.

The linter also applies the same review-posture coherence used by fresh-session
resume trust:

- HANDOFF cannot say `Review-required items: none` while VERIFY is
  `REVIEW_REQUIRED`;
- HANDOFF cannot carry review-required verification items while VERIFY is
  `PASS`.

This is content reconciliation only. Handoff freshness and required-file checks
remain owned by the fresh-session trust gate.

## Status semantics

### PASS

All active cross-artifact contracts agree.

Optional relationships that are not active report `NOT_APPLICABLE` and do not
downgrade the aggregate result.

### FAIL

Reserved for a clear contradiction already treated as failure by an underlying
contract, such as:

- an active contract ID mismatch;
- acceptance evidence explicitly reporting `FAIL`;
- a required compatibility probe explicitly failing.

### REVIEW_REQUIRED

Used when consistency cannot be established safely, for example:

- an active coverage or compatibility relationship is incomplete;
- SPEC and SCOPE file budgets disagree;
- VERIFY and SCOPE disagree about whether the scope gate applies;
- HANDOFF verification state disagrees with VERIFY.

Exit codes:

- `0` — PASS
- `1` — FAIL
- `2` — REVIEW_REQUIRED

## Relationship to other tools

This linter does **not** replace:

- `spec_gate.py` for SPEC quality;
- `scope_gate.py` for enforcing the live Git diff;
- `verify_gate.py` for deterministic verification and diff guards;
- `acceptance_coverage.py` for detailed AC-ID coverage;
- `check_contract_lineage.py` for contract-generation identity;
- `resume_trust.py` for fresh-session handoff trust;
- `workflow_doctor.py` for selecting the safest next move.

The point is narrower: catch states where individually plausible durable
artifacts tell different stories.

## Claim boundary

A `PASS` means the active deterministic relationships checked here are mutually
consistent. It does not prove that the artifacts are correct, complete, fresh,
authorized, or sufficient to establish implementation correctness.
