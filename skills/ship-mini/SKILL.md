# Ship Mini

## Purpose

Decide whether a small project, dashboard, ML workflow, or agent workflow is safe to use.

## When to use

Use before user-facing release, scheduled runs, autonomous agent execution, decision-impacting analysis, or sharing outputs with others.

## Inputs

- `SPEC.md`
- `VERIFY.md`
- Changed files
- Test/build/lint results
- Data/model/agent context if relevant

## Workflow

1. Create or update `SHIP.md`.
2. Check user-facing behavior.
3. Check test, build, and lint commands.
4. Check data freshness if relevant.
5. Check row counts, nulls, and metric deltas if relevant.
6. Check model artifact/version if relevant.
7. Check agent tool permissions if relevant.
8. Define rollback path.
9. Note owner notification if relevant.
10. Decide GO or NO-GO.

## Outputs

- `SHIP.md`
- GO / NO-GO decision
- Blockers
- Accepted risks
- Rollback plan

## Stop conditions

- A GO / NO-GO decision is recorded.
- A blocker requires more implementation or verification.

## Anti-patterns

- Calling something shipped just because the implementation task passed.
- Ignoring data freshness or permissions for automated workflows.
- Shipping without a rollback path.
