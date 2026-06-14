# Verify Contract

## Verification status

Illustrative walkthrough only. This example does not include an executable fixture.

## Expected verification record

A real implementation should record:

- exact command run
- exact command result from the local run
- changed files
- untested risks
- next safest task

## Example command shape

Replace this with the smallest relevant project check:

```bash
npm test -- auth-session-state
```

## Changed files

Expected for a real implementation:

- selected auth helper or login-state file
- directly related auth test file

## Not tested

- full browser login flow unless explicitly run
- dashboard usability changes, because they are out of scope

## Remaining risks

- the selected unit test may not cover the full login/logout path
- a separate dashboard usability mini-spec is still needed

## Next safest task

Create a separate mini-spec for dashboard usability if that work is still desired.
