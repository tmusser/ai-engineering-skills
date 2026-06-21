---
name: ship-mini
description: Run a lightweight GO or NO-GO gate before use, especially for autonomous or scheduled workflows.
---

# Ship Mini

## Purpose

Decide whether a small project, dashboard, ML workflow, or agent workflow is ready to use.

## When to use

Use before user-facing release, scheduled runs, autonomous agent execution, decision-impacting analysis, or sharing outputs with others.
Use when an agent will write, send, trigger, or act with tools on your behalf.

## Inputs

- `SPEC.md`
- `VERIFY.md`
- Changed files
- Test/build/lint results
- Data/model/agent context if relevant
- Allowed tools
- Forbidden tools or actions
- Destructive operations
- Secrets and credentials
- PII or sensitive data access
- Dry-run mode
- Human approval gates
- Audit logging
- Rollback path
- Owner notification
- Stop conditions

## Workflow

1. Create or update `SHIP.md`.
2. Check user-facing behavior or the scheduled/autonomous action.
3. If the run can write, send, or trigger actions, record allowed tools, forbidden tools or actions, destructive operations, secrets and credentials, PII or sensitive data access, dry-run mode, human approval gates, audit logging, rollback path, owner notification, and stop conditions.
4. Check test, build, and lint commands.
5. Check data freshness if relevant.
6. Check row counts, nulls, and metric deltas if relevant.
7. Check model artifact/version if relevant.
8. Check agent tool permissions if relevant.
9. Decide GO or NO-GO.

## Outputs

- `SHIP.md`
- GO / NO-GO decision
- Blockers
- Accepted risks
- Rollback plan

## Stop conditions

- A GO / NO-GO decision is recorded.
- A required approval, dry-run, or rollback path is still unclear.
- A blocker requires more implementation or verification.

## Anti-patterns

- Calling something shipped just because the implementation task passed.
- Ignoring data freshness or permissions for automated workflows.
- Shipping without a rollback path.
- Treating autonomous or scheduled runs like interactive sessions.
