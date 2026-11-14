# Decisions

This ledger is optional. Capture only consequential, durable choices that another
session must preserve. Ordinary implementation steps, hypotheses, open questions,
and one-action workspace checkpoints do **not** belong here.

Keep stable IDs (`D1`, `D2`) and append successors instead of overwriting
historical rationale. To replace `D1`, mark it `SUPERSEDED`, append `D2`,
and set `Supersedes: D1`. Cite existing authority; this ledger does not
grant decision-making permission or override `SPEC.md`.

Copy this entry shape **out of the fence** when a durable decision is warranted:

~~~markdown
## D1: Preserve the existing CSV column order

- Status: ACTIVE
- Date: 2026-11-14
- Authority: Accepted SPEC.md compatibility requirement
- Why: Downstream clients rely on positional column semantics.
- Alternatives: Reorder columns; rejected because it breaks clients.
- Evidence: SPEC.md compatibility seam; tests/test_export.py.
- Consequences: Any export change must preserve the column sequence.
- Revisit if: Consumers approve a versioned schema migration.
- Supersedes: none
~~~

Use `python scripts/aes.py decisions` to check formatting, references, and
supersession consistency. This read-only check cannot validate substantive
authority, test evidence, or whether a decision is correct. See
[Decision ledger](../docs/decision-ledger.md).
