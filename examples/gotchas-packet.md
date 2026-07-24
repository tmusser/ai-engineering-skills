# Gotchas Packet Example

This example shows the optional artifact without adding it to the starter workflow.

Project `GOTCHAS.md`:

```text
# Gotchas

## G1 - Export filter keeps no-match behavior

- Trigger: changing dashboard export filters
- Gotcha: the no-match branch intentionally returns the existing empty export shape
- Consequence: simplifying the branch changes a compatibility seam
- Safe path: preserve the empty shape and run the no-match fixture
- Evidence: tests/test_export.py::test_no_match_export
- Last verified: 2026-07-24
- Status: active
```

Explicit packet generation when that sharp edge matters:

```bash
python scripts/context_pack.py \
  "resume the dashboard export change without crossing known sharp edges" \
  --require-file GOTCHAS.md \
  --strict
```

Expected packet metadata includes:

```text
Required sources: GOTCHAS.md=represented
```

The selected-context table then records the `GOTCHAS.md` range and content hash. The
artifact remains optional; an unrelated task should not load it merely because it exists.
