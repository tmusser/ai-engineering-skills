# Decision Ledger

`DECISIONS.md` is an **optional** task-state artifact for consequential choices
that must survive sessions or prevent a later agent from reopening a settled
tradeoff without recognizing it. It is not a new workflow gate and should not
be created simply because work involves a decision.

## What belongs here

Capture a decision when **all** of these hold:

1. A concrete choice was made within existing authority.
2. A credible alternative or tradeoff mattered to the outcome.
3. Another session or contributor must preserve or deliberately revisit it.

Keep speculative choices and unresolved proposals in `SPEC.md` open questions or
`HANDOFF.md` open decisions. Use the ephemeral `workspace-checkpoint` for the
next consequential action; do not persist every checkpoint.

## Minimal durable entry

Use a single stable ID and concise one-line fields. Copy the format in
[DECISIONS.md template](../templates/DECISIONS.md).

~~~markdown
## D1: Preserve the existing CSV column order

- Status: ACTIVE
- Date: 2026-11-14
- Authority: Accepted SPEC.md compatibility requirement
- Why: Consumers use positional column semantics.
- Alternatives: Reorder columns; rejected due to compatibility risk.
- Evidence: SPEC.md compatibility seam; tests/test_export.py.
- Consequences: Export refactors must preserve the original order.
- Revisit if: Consumers approve a versioned migration.
- Supersedes: none
~~~

`Authority` identifies where the choice is **permitted or approved**. It does
not mean the ledger grants permission. `Evidence` identifies where factual
support can be inspected; a path or assertion alone is not verified proof.
`Revisit if` is a concrete invalidation condition, not an expiry date.

The entry title is the adopted outcome, not a proposal. Keep it short; capture
the rationale and rejected alternatives once rather than a meeting transcript.

## Lifecycle and replacement

Never silently rewrite historical reasoning to match a new implementation.

For a new decision replacing D1:

1. Change **only** D1's `Status` to `SUPERSEDED` (keep its rationale and date).
2. Append D2 with the new outcome, evidence, authority, and tradeoffs.
3. Set `D2`'s `Supersedes: D1`. Leave D2 `ACTIVE`.

One earlier decision can have **one direct successor**. The successor may itself
be superseded later, creating a transparent chain. Do not delete old entries,
reuse IDs, split one superseded decision into multiple untracked successors, or
treat a superseded choice as a current instruction. If multiple independent
choices are needed, record them separately rather than forging a branching
history.

If a decision no longer applies, record the new action or policy as the
replacement decision instead of erasing the old choice.

## Optional read-only check

~~~bash
python scripts/aes.py decisions --decisions DECISIONS.md
python scripts/aes.py decisions --format json
~~~

The checker verifies known one-line fields, IDs, dates, structural completeness,
and **one-to-one backwards supersession**. It reports missing justification,
duplicate IDs, bad status, invalid date, dangling or competing successors,
and old ACTIVE decisions that a newer entry claims to supersede.

| Status | Exit | Meaning |
| --- | --- | --- |
| `PASS` | 0 | Structural requirements satisfied |
| `NOT_APPLICABLE` | 0 | No ledger or no live decision entries |
| `REVIEW_REQUIRED` | 3 | A malformed or incoherent ledger needs review |
| Input error | 2 | The ledger cannot be read |

This is a structural check, **not** evidence verification or an authorization
gate. `PASS` does not prove the authority was valid, the evidence is fresh, or
the tradeoff was wise. It does not run by default inside `verify_gate.py` or
change repository completion status. Run it when durable decisions warrant it.

## Handoff and authority

When a durable decision governs the next task, `HANDOFF.md` should reference
the **active D-ID** and include `DECISIONS.md` among its read-first sources.
Do not copy the whole ledger into the handoff. At resume, compare the referenced
decision against live `SPEC.md`, code, tests, and current operator instructions;
the ledger cannot override them. If they conflict, stop and resolve the conflict
rather than silently promoting historical notes into authoritative truth.

This is a task-level artifact, not a long-term memory database or a new
permission system. For short reversible changes, skip the ledger entirely.
