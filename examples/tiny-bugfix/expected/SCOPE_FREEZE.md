# Scope Freeze

## Task

Add a `--limit` flag to the tiny discount CLI example.

## Allowed

- `examples/tiny-bugfix/after/discount_cli.py`
- `examples/tiny-bugfix/after/test_discount_cli.py`

## Read-only

- `examples/tiny-bugfix/before/`
- `examples/tiny-bugfix/expected/`

## Forbidden

- Changing installers.
- Adding dependencies.
- Touching unrelated examples.

## Max files

2

## Allowed commands

- `python -m unittest discover examples/tiny-bugfix/after`

## Stop when

The after suite passes with `--limit 2`.
