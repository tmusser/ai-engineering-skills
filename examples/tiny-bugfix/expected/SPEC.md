# SPEC

## Objective

Add a `--limit` flag to the tiny discount CLI so it prints only the first N discount rows.

## User / use case

Someone wants a quick preview of discount rows without reading the full table.

## Acceptance criteria

- `python -m unittest discover examples/tiny-bugfix/after` passes.
- `--limit 2` prints only the first two data rows.
- Omitting `--limit` keeps the full output.

## Non-goals

- No database access.
- No formatting overhaul.
- No new dependencies.

## Constraints

- Python standard library only.
- Use `unittest`, not `pytest`.
- Keep the example self-contained.

## Commands

- `python -m unittest discover examples/tiny-bugfix/before`
- `python -m unittest discover examples/tiny-bugfix/after`

## Project structure

- `before/` reproduces the missing behavior.
- `after/` contains the fix and passing test.
- `expected/` holds the copy/paste artifacts.

## Verification demo

- Run `python -m unittest discover examples/tiny-bugfix/after`
- Confirm the suite passes and only the first two rows print.

## Open questions

- None.
