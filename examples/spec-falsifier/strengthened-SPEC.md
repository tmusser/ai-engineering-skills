# Spec: Filter CSV Orders by Region (Strengthened)

## Objective

Add an optional region filter to orders CSV without changing preserved behavior.

## Authoritative references

| Reference | Governs | Task-specific delta |
| --- | --- | --- |
| `examples/spec-falsifier/README.md` | Original request, headers, and empty-match semantics | none |

## Acceptance criteria

- For region East, CSV contains every matching order once and no orders
  from another region, preserving existing column names and order.
- For a region with zero matching orders, return a header-only CSV with
  the same existing column names and order and no data rows.

## Non-goals

- No new CSV columns, dependencies, or alternate export formats.

## Spec ceiling

Implement only the region filter and its required compatibility behavior.

## Likely failure modes

Primary failure mode for this slice:

> Happy-path export succeeds while zero-match output drops the existing header.

## Verification demo

- Check East rows and original column order.
- Run an unmatched region export and assert header-only output with no data rows.

## Open questions

- None

## Invalid if

- Changes CSV headers, order, or no-match semantics; adds unrelated formats.
