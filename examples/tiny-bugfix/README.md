# Tiny Bugfix: `--limit`

This example shows a three-minute workflow on a tiny CLI bugfix.

The `before/` suite fails on purpose because the CLI does not support `--limit` yet. The `after/` suite passes once the flag is added.

## Minimum viable loop

mini-spec -> thin-plan -> scope-freeze -> build-one -> verify-contract -> handoff

## Run it

```bash
python -m unittest discover examples/tiny-bugfix/before
python -m unittest discover examples/tiny-bugfix/after
```

The first command should fail. The second should pass.

## Files

- `before/` reproduces the missing behavior.
- `after/` contains the fix.
- `expected/` shows the compact artifacts an agent should write.
