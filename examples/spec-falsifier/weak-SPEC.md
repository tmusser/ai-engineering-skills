# Spec: Filter CSV Orders by Region (Weak)

## Objective

Add an optional region filter to the existing orders CSV export.

## Acceptance criteria

- With matching orders in region East, an export with `region=East` includes
  those rows in CSV format.

## Non-goals

- Do not add new CSV columns or dependencies.

## Spec ceiling

Implement only the optional region filter; do not redesign the CSV interface.

## Likely failure modes

Primary failure mode for this slice:

> Returning records from the wrong region for a matching export.

## Verification demo

- Export for region East (known matching rows) and inspect the returned CSV.

## Open questions

- None

## Invalid if

- Adds unrelated export formats or changes existing column names.
