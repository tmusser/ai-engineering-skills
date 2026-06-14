# Scope Freeze

## Allowed files

- `auth/**`
- `tests/auth/**`

## Read-only files

- `dashboard/**`
- `layout/**`

## Forbidden operations

- Dashboard UI changes
- Schema changes
- Opportunistic cleanup outside auth

## Max files changed

- 3

## Max lines changed

- 80

## Allowed commands

- `python -m unittest discover examples/broken-vs-gated/gated`

## Stop condition

Stop after the auth slice passes verification.
