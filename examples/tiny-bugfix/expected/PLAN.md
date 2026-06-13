# PLAN

## Implementation slices

1. Reproduce the missing `--limit` behavior in a failing before test.
2. Add `--limit` parsing and row slicing in the after CLI.
3. Verify the after suite passes.

## Dependencies

- No external dependencies.
- Standard library only.

## Risk notes

- Keep the CLI output deterministic.
- Keep the example tiny and isolated.

## Verification strategy

- `python -m unittest discover examples/tiny-bugfix/before`
- `python -m unittest discover examples/tiny-bugfix/after`
