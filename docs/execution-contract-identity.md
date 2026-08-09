# Optional Execution Contract Identity

Some delegated, autonomous, or multi-session tasks benefit from a stable identity that
links the original task contract to later replans and verification records.

This repository keeps that identity lightweight and optional. It does not require a
new runtime, signing service, or contract database.

## Minimal fields

Record these fields in `SPEC.md` only when they buy back traceability:

```text
Contract ID: task-...
Parent contract ID: task-... | none
Base commit: <git sha or unknown>
Issued at: <ISO-8601 timestamp or date>
Replan reason: <why a new contract was issued or none>
```

## When to use

Use contract identity when:

- another agent or session will execute the task later;
- an autonomous worker needs an immutable authorization reference;
- scope is renegotiated after implementation has started;
- several verification records must be tied to one declared task contract;
- a failed route is replaced and the relationship between attempts matters.

## When not to use

Skip it for tiny reversible edits, one-session patches, or work that already has an
unambiguous issue or task identifier.

Do not add identity fields merely to prove that ceremony occurred.

## Replanning rule

Do not silently rewrite the meaning of an active contract after scope, permissions, or
acceptance criteria materially change.

Instead:

1. preserve the prior contract identifier;
2. issue a new contract identifier;
3. set the prior identifier as the parent;
4. record the replan reason;
5. re-run the cheapest relevant scope and verification checks.

`Supersedes contract ID` is accepted as an equivalent parent-lineage label when a
workflow prefers that wording.

This creates a small lineage trail without turning `SPEC.md` into an event log.

## Propagation rule

`SPEC.md` owns whether contract identity is active.

When SPEC has no meaningful `Contract ID`, downstream artifacts do not need identity
fields. This is the normal case for small work.

Once SPEC opts in, every downstream durable artifact that exists for the active task
should carry exactly the same active contract ID:

- `PLAN.md` when a plan is created;
- `VERIFY.md` when verification evidence is recorded;
- `HANDOFF.md` when continuation state is created.

A downstream artifact must not continue to name the parent after a replan. That mixes
evidence from different task generations even when each artifact looks individually
plausible.

## Deterministic lineage check

Run:

```bash
python scripts/check_contract_lineage.py
```

or through the unified CLI:

```bash
python scripts/aes.py lineage
```

The checker is deliberately opt-in by data rather than by command. If SPEC has no
contract ID and no contradictory downstream ID is present, it returns `PASS` with
lineage enforcement inactive.

When identity is active, the checker validates:

- one active SPEC contract ID;
- matching IDs in existing PLAN / VERIFY / HANDOFF artifacts;
- parent/supersedes not equal to the active ID;
- a meaningful replan reason when a parent exists;
- locally resolvable base-commit provenance.

Status semantics:

- `PASS` — no identity is active, or the active lineage is internally consistent;
- `FAIL` — a clear contradiction exists, such as mismatched, obsolete-parent, multiple,
  or self-parenting IDs;
- `REVIEW_REQUIRED` — lineage cannot be established, such as a missing downstream ID or
  unresolved base commit.

See [Contract lineage checker](contract-lineage.md) for the exact boundary.

## Relationship to existing artifacts

- `SPEC.md` owns the task contract and optional identity.
- `PLAN.md` carries the active contract ID when identity is enabled and a plan exists.
- `VERIFY.md` carries the active contract ID when identity is enabled.
- `HANDOFF.md` carries the active contract ID when identity is enabled and continuation
  state exists.
- Git history remains the source of truth for file changes and commits.

## Enforcement boundary

These fields are identifiers, not security controls.

They do not:

- cryptographically sign the task;
- prevent an agent from editing outside scope;
- replace permissions, sandboxing, or runtime authorization;
- prove that the recorded base commit was the semantically correct authorization point;
- require hooks or runtime interception.

The lineage checker can establish that a recorded base resolves locally and is an
ancestor of current `HEAD`; it cannot prove that the human intended that particular
commit as the correct base.

The portable Markdown workflow remains useful without any runtime hook.

## Example

```text
Contract ID: task-dashboard-export-02
Parent contract ID: task-dashboard-export-01
Base commit: 4f2a91c
Issued at: 2026-07-23
Replan reason: existing CLI compatibility seam was discovered after the first slice
```

The identifier makes the contract lineage inspectable. The actual acceptance criteria,
scope boundary, invalidators, and verification evidence still determine whether the
work is safe to accept.
