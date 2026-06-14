# Clarified Request

Clean up the auth flow in this slice. Leave dashboard usability for a separate slice.

## Domain terms

- auth flow: login, redirect, session state, and post-refresh behavior
- cleanup: remove duplicate login-state handling
- dashboard usability: a later slice with its own acceptance criteria

## Decisions

- The current slice is auth only.
- Dashboard changes are out of scope.

## Assumptions

- The auth issue is bounded to login-state handling.
- Existing auth behavior should continue to work after the cleanup.

## Non-goals

- Dashboard redesign.
- Broader app-wide refactors.

## Unresolved questions

- Which dashboard usability issue should be handled next?

## Readiness judgment

Ready for a thin plan on the auth slice.
