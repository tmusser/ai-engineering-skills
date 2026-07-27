---
name: ship-mini
description: Run a lightweight activation GO or NO-GO gate only when verified work is about to gain material real-world side effects, autonomy, permissions, or production/shared-state impact.
---

# Ship Mini

## Purpose

Decide whether verified work is safe and authorized to activate in a real operating environment.

`verify-contract` owns correctness and evidence. `ship-mini` does not re-verify the implementation; it owns the additional operational question: should this verified thing be allowed to act on the world now?

## When to use

Use after verification when activation introduces one or more material operational risks:

- production or shared-state writes
- scheduled, autonomous, or unattended execution
- sending, publishing, triggering jobs, or other external side effects
- new or expanded tool permissions
- secrets, credentials, PII, or sensitive-data access
- destructive or difficult-to-reverse actions
- a required human approval boundary
- a meaningful rollback, audit, or owner-notification requirement

Skip `ship-mini` for ordinary local or interactive changes whose effects remain reviewable and reversible. A user-facing change, shared report, dashboard update, model result, or successful `verify-contract` does not require `ship-mini` merely because it may be released or seen by others.

Do not create `SHIP.md` when no material activation risk exists.

## Inputs

- `VERIFY.md` status and evidence reference
- What will be activated and where
- Allowed tools / actions
- Forbidden tools / actions
- Target environment or shared state
- Destructive or irreversible operations
- Secrets, credentials, PII, or sensitive-data scope
- Dry-run or staged activation path when relevant
- Human approval gates
- Audit logging
- Rollback / disable path
- Owner notification
- Stop conditions

## Workflow

1. Confirm the implementation already has sufficient verification evidence. Reference `VERIFY.md`; do not replay correctness checks merely because `ship-mini` is invoked.
2. Classify activation risk:
   - `NONE` — no material side effect, autonomy, permission, data, or rollback boundary exists. Stop without creating `SHIP.md`.
   - `PRESENT` — one or more material activation risks exist. Continue.
3. Name the exact activation surface: what will run, write, send, publish, trigger, access, or mutate, and in which environment.
4. Record allowed and forbidden actions, permission/data boundaries, destructive operations, and required human gates.
5. Confirm the smallest practical dry-run or staged activation path when one exists.
6. Confirm rollback or disable path before irreversible or shared-state effects are enabled.
7. Confirm audit logging, owner notification, and stop conditions when unattended or externally visible effects are possible.
8. Resolve any `REVIEW_REQUIRED` verification item that affects activation safety. A functional `FAIL` cannot be shipped.
9. Create or update `SHIP.md` with the activation decision and only the operational evidence needed for `GO` / `NO-GO`.

Do not rerun tests, builds, lint, data-quality checks, or model validation unless activation changed the environment or inputs in a way that invalidates the existing verification evidence.

## Activation gate

Status: GO | NO-GO

- `GO` only when verification is trustworthy for the activated state and every material activation boundary is explicit enough to operate safely.
- `NO-GO` when a required approval, permission boundary, data boundary, rollback path, audit path, owner notification, or stop condition is unresolved.
- `NO-GO` when verification is `FAIL`.
- `REVIEW_REQUIRED` verification may proceed only after a human explicitly resolves or accepts the item and it does not hide a functional failure.

## Outputs

When activation risk is `PRESENT`:

- `SHIP.md`
- GO / NO-GO decision
- Activation surface
- Operational blockers
- Accepted operational risks
- Human gates
- Rollback / disable path
- Audit / notification / stop conditions when relevant

When activation risk is `NONE`:

- No `SHIP.md`
- Continue from verification to the next appropriate workflow step

## Stop conditions

- Activation risk is `NONE`; skip the skill artifact.
- `GO` is recorded with operational boundaries explicit.
- `NO-GO` is recorded because a material activation boundary remains unresolved.

## Anti-patterns

- Running `ship-mini` after every successful `verify-contract`.
- Re-running correctness checks already captured in `VERIFY.md` without evidence they became stale.
- Treating ordinary release, sharing, or visibility as activation risk by itself.
- Creating `SHIP.md` when no material side effect or operational boundary exists.
- Shipping autonomous or external side effects without approval, rollback, audit, or stop conditions appropriate to the risk.
