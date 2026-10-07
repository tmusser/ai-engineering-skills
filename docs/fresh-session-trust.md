# Fresh-Session Trust Gate

A fresh agent should not treat `HANDOFF.md` as authoritative merely because the
file exists or its Git fingerprint is fresh.

The handoff freshness guard answers one question:

> Did non-handoff repository state change after this packet was stamped?

The fresh-session trust gate answers the next question:

> Is this still a coherent packet to resume from?

## Command

Run from the repository root:

```bash
python skills/handoff/scripts/resume_trust.py check \
  --handoff HANDOFF.md \
  --verify VERIFY.md
```

The gate is read-only. It composes the existing handoff freshness check with
content reconciliation.

## PASS contract

`HANDOFF RESUME TRUST: PASS` requires:

- handoff freshness is `PASS`;
- every path listed in `Required resume files` exists;
- `Verify gate status` in the handoff matches the live recorded status in
  `VERIFY.md`, including explicit `NOT_PRESENT`;
- `Review-required items` is coherent with the live verify state;
- exactly one next recommended task is present;
- the verification state contains a next verification command.

A freshness `PASS` is necessary but not sufficient. Because `HANDOFF.md`
itself is intentionally excluded from the workspace fingerprint, the packet can
be edited after stamping without changing freshness. The trust gate catches
self-contradictory or incomplete continuation claims before they become action.

## Status semantics

- `PASS` — snapshot and continuation claims are coherent enough to resume.
- `STALE` — repository state changed after the snapshot. Re-read live state and
  regenerate the handoff.
- `REVIEW_REQUIRED` — the snapshot may be fresh, but the packet cannot be
  trusted yet because required references, verification state, unresolved-item
  posture, or next-step fields do not reconcile.

Exit codes are `0` for `PASS`, `2` for `STALE`, and `3` for
`REVIEW_REQUIRED`.

## Required resume files

Use `Required resume files` for artifacts or source files the next task truly
depends on, not every file mentioned in the handoff.

Example:

```text
Required resume files: SPEC.md, VERIFY.md, src/export.py
```

The gate checks that every listed path is a safe repository-relative file and
still exists. This is deliberately narrower than scraping arbitrary Markdown
links or every filename-looking token from the handoff.

## Verification reconciliation

The handoff records the expected live state:

```text
- Verify gate status: PASS
- Review-required items: none
```

The gate compares the expected status to the live recorded `VERIFY.md` status.

If live verification is `REVIEW_REQUIRED`, the handoff cannot claim there are
no review-required items. If live verification is `PASS`, the handoff cannot
continue carrying stale review-required items as though they remain unresolved.

This is a coherence check, not a replacement for `verify-contract` or
`scripts/verify_gate.py`.

## Workflow doctor integration

`scripts/workflow_doctor.py` uses the resume-trust gate for an existing
`HANDOFF.md`. A next task from the handoff is trusted only after resume trust
returns `PASS`.

That means a handoff with a fresh fingerprint but a missing required file or
mismatched verification claim cannot nominate the next action.

## Migration

Existing handoffs that do not record `Required resume files`, exact
`Verify gate status`, `Review-required items`, one next task, and a next
verification command will return `REVIEW_REQUIRED` under the fresh-session
trust gate.

Regenerate the handoff with the current template rather than silently treating
an older packet as authoritative.

## Claim boundary

A `PASS` means the packet is internally coherent with the live repository and
recorded verification state under these checks. It does not prove that the
specification, verification, or next task is substantively correct.
