# Thin Plan

## Slice 1

Remove duplicate login-state handling from auth middleware.

- Files: auth middleware and auth tests
- Observable result: sign-in behavior stays stable after refresh

## Slice 2

Do not include dashboard usability in this pass.

## Verification

- Run the auth-focused unit tests.
- Confirm the dashboard slice is still untouched.
