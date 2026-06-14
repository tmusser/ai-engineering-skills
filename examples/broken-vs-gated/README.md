# Broken vs Gated Example

This walkthrough shows why the gates exist.

## Scenario

A vague request produces a plausible plan that is broader than the intended work.

Request:

> Clean up the auth flow and make the dashboard easier to use.

## Run A: ungated

The agent produces a reasonable-looking plan, but silently expands scope:

- touches auth middleware
- changes dashboard layout
- removes utility code
- updates tests after implementation
- reports success without a clear original acceptance contract

Result:

- code may pass checks
- the user still cannot tell whether the right work was done
- unrelated changes make review harder
- follow-up work starts from fuzzy state

See: [`ungated/`](./ungated/)

## Run B: gated

The workflow catches the ambiguity before implementation.

### `mini-spec`

Clarifies that this is not one task. It splits the request into:

1. auth cleanup
2. dashboard usability

Only one is selected for the current slice.

### `grill-with-docs-lite`

Checks overloaded terms:

- "cleanup" means remove duplicate login-state handling, not redesign auth
- "easier to use" is deferred because it needs a separate acceptance criterion

### `thin-plan`

Creates the smallest safe route for the selected slice.

### `scope-freeze`

Limits allowed files and forbids opportunistic UI or schema changes.

### `verify-contract`

Records exact commands, results, changed files, known risks, and what was not tested.

See: [`gated/`](./gated/)

## Lesson

The gated run is not valuable because it adds ceremony.

It is valuable because it catches the wrong-work failure before the agent spends tokens and edits files.
