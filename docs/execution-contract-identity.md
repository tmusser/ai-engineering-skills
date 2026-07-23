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

- another agent or session will execute the task later
- an autonomous worker needs an immutable authorization reference
- scope is renegotiated after implementation has started
- several verification records must be tied to one declared task contract
- a failed route is replaced and the relationship between attempts matters

## When not to use

Skip it for tiny reversible edits, one-session patches, or work that already has an
unambiguous issue or task identifier.

Do not add identity fields merely to prove that ceremony occurred.

## Replanning rule

Do not silently rewrite the meaning of an active contract after scope, permissions, or
acceptance criteria materially change.

Instead:

1. preserve the prior contract identifier
2. issue a new contract identifier
3. set the prior identifier as the parent
4. record the replan reason
5. re-run the cheapest relevant scope and verification checks

This creates a small lineage trail without turning `SPEC.md` into an event log.

## Relationship to existing artifacts

- `SPEC.md` owns the task contract and optional identity.
- `VERIFY.md` should name the contract ID when several contracts or replans exist.
- `HANDOFF.md` should carry the active contract ID only when continuation depends on it.
- Git history remains the source of truth for file changes and commits.

## Enforcement boundary

These fields are identifiers, not security controls.

They do not:

- cryptographically sign the task
- prevent an agent from editing outside scope
- replace permissions, sandboxing, or runtime authorization
- prove that the recorded base commit is correct

A runtime may later bind these fields to stronger enforcement, but the portable
Markdown workflow should remain useful without that runtime.

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
