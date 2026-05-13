# ML Model POC

## Scenario

Build a small model workflow that predicts trial conversion from a tabular feature set and writes an evaluation report.

## Workflow

1. Use `grill-with-docs-lite` to define target, prediction horizon, leakage risks, and feature ownership.
2. Use `mini-spec` to document data split, feature schema, baseline, metric, and artifact path.
3. Use `thin-plan` to create slices: fixture dataset, feature validation, baseline model, metric report, artifact write.
4. Use `scope-freeze` to limit edits to the model workflow, fixtures, and tests.
5. Use `build-one` to implement feature schema validation first.
6. Use `test-mini` with a fixture dataset that includes missing values, unexpected columns, and known labels.
7. Use `verify-contract` to record metric calculation, baseline comparison, and artifact/version.
8. Use `ship-mini` before scheduling training or using the report for decisions.

## Concrete checks

- Data split is deterministic and documented.
- Feature schema rejects missing required columns.
- Metric calculation is tested against a small known example.
- Baseline comparison is recorded before claiming model improvement.
- Ship gate records data freshness, model artifact/version, accepted risks, and rollback path.
