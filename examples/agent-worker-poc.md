# Agent Worker POC

## Scenario

Build an autonomous worker that reads a Monday board or ticket board, drafts a
branch/PR for one approved task type, and stops for human review.

## Workflow

1. Use `grill-with-docs-lite` to clarify intake fields, autonomy level, allowed task type, and stop conditions.
2. Use `mini-spec` to define accepted input, allowed files, forbidden operations, and PR output.
3. Use `thin-plan` to create slices: board intake parser, dry-run planner, branch creation, PR summary, permission gate.
4. Use `scope-freeze` before each slice with explicit allowed tools and files.
5. Use `build-one` to implement only the dry-run planner first.
6. Use `test-mini` with fixture ticket data and a deterministic expected plan.
7. Use `verify-contract` to record the dry-run command and output.
8. Use `ship-mini` to review tool permissions before enabling writes.

## Concrete checks

- Fixture ticket includes title, body, labels, repo path, and acceptance criteria.
- Verification command produces the same plan for the same fixture.
- Branch/PR output is disabled until the ship gate says GO.
- Ship gate records allowed boards, allowed repos, write permissions, rollback, and owner notification.
