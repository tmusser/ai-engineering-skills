# Spec

## Objective

Clean up the auth flow in one bounded slice without pulling dashboard usability into the same change.

## User / use case

A user signs in, refreshes the app, and keeps a stable auth state.

## Acceptance criteria

- Duplicate login-state handling is removed.
- Auth success and failure paths still work.
- Dashboard layout is unchanged in this slice.

## Non-goals

- Dashboard usability changes.
- New auth providers or sign-in flows.
- Broad cleanup outside auth state handling.

## Likely failure modes

Check the risks this spec is meant to prevent.

- [ ] Premature agreement on vague scope
- [ ] Hidden non-goals
- [ ] Over-broad file changes
- [ ] Unclear acceptance criteria
- [ ] Unverified success claim
- [ ] Context drift / forgotten constraint
- [ ] Hallucinated dependency or API behavior
- [ ] Refactor disguised as a small fix
- [ ] Multiple tasks bundled as one request
- [ ] Other: dashboard usability sneaking into this slice

Primary failure mode for this slice:

> Bundling dashboard usability into the auth cleanup.

If none apply, use a lighter workflow.

## Constraints

- Change only auth middleware and auth tests.
- Keep the patch small enough to review quickly.

## Commands

- Run: `python -m unittest discover examples/broken-vs-gated/gated`
- Test: `python -m unittest discover examples/broken-vs-gated/gated`
- Verify: `python -m unittest discover examples/broken-vs-gated/gated`

## Project structure

- auth middleware
- auth tests

## Verification demo

Show one passing command and one short note about the unchanged dashboard slice.

## Open questions

- None for this slice.
