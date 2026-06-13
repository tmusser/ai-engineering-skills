# Handoff

## Resume packet

Read first if present:
- `HANDOFF.md`
- `SPEC.md`
- `PLAN.md`
- `VERIFY.md`

Resume command:
- `python -m unittest discover examples/tiny-bugfix/after`

## Workflow state

Active modes:
- lean-mode: off
- context-check: off

Current phase:
- complete

Current loop:
- verify example output

Next gate:
- handoff

Context risk:
- low

Active hypothesis:
- none

## Project goal

- Show the workflow value of a tiny CLI bugfix in three minutes.

## Current status

- Before suite fails intentionally.
- After suite passes.

## State IDs

Facts:
- F1: `--limit` truncates the CLI output.

Decisions:
- D1: Use the Python standard library and `unittest` only.

Assumptions:
- A1: The example stays self-contained under `examples/tiny-bugfix/`.

Claims / numbers:
- C1: `python -m unittest discover examples/tiny-bugfix/after` passes.

## Completed slices

- Built before and after versions of the CLI and tests.
- Wrote copy/paste-friendly expected artifacts.

## Changed files

- `after/discount_cli.py`: implements `--limit`.
- `after/test_discount_cli.py`: verifies truncation.
- `before/discount_cli.py`: reproduces the missing behavior.
- `before/test_discount_cli.py`: demonstrates the missing behavior.

## Commands that work

- `python -m unittest discover examples/tiny-bugfix/after`

## Known failing commands

- `python -m unittest discover examples/tiny-bugfix/before`

## Verification state

Last proof:
- `python -m unittest discover examples/tiny-bugfix/after` passed.

Next verification command:
- `python -m unittest discover examples/tiny-bugfix/after`

## Open decisions

- None.

## Traps / do-not-change notes

- Keep the before failure intentional.
- Do not add dependencies.

## Next recommended task

- Use this example as the first smoke test for new users.
