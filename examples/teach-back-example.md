# Teach Back Example

A focused example of transferring ownership after a verified implementation.

## Situation

A dashboard export endpoint now supports CSV while preserving the existing JSON response.

Verification has already passed:

- focused CSV export tests pass;
- the legacy JSON compatibility test passes;
- the verify gate reports `PASS`.

The human expects to maintain the export path but did not write the implementation.

## Implementation map

```text
GET /export?format=csv
  -> export_dashboard route
  -> format validation
  -> shared row builder
  -> CSV serializer
  -> response headers and body
  -> focused CSV and legacy JSON tests
```

Observed:

- `export_dashboard` selects the serializer from the requested format.
- CSV and JSON share the same row-building function.
- The compatibility test locks the previous JSON shape.

Inferred:

- The shared row builder was chosen to prevent the two formats from drifting.

Open:

- The implementation does not document whether new formats should reuse the same row model.

## Teach-back prompt

```text
Before I explain the implementation in full:

1. What path does a CSV request take from route to response?
2. Why is the shared row builder important?
3. If JSON values changed but CSV remained correct, where would you investigate first?
```

## Human attempt

```text
The route checks the requested format, builds the export rows, and sends them to the
CSV serializer. Sharing the rows keeps CSV and JSON consistent. If only JSON changed,
I would first inspect the JSON serializer or its response formatting rather than the
shared row builder.
```

## Targeted correction

The explanation is materially correct. One missing detail matters: format validation happens before the shared row builder, so an unsupported format should fail without doing export work.

Evidence: the route rejects unknown formats before calling `build_export_rows`, and the focused invalid-format test asserts that behavior.

## Transfer question

```text
Suppose product asks for XLSX export with the same columns but different type handling.
Which part should probably remain shared, which part should be format-specific, and what
compatibility test would you add before implementation?
```

## Ownership check

```text
behavior path understood: yes
main trade-off understood: yes
likely failure seam understood: yes
remaining gap: confirm and document the extension rule before adding another format
```

## What this example does not do

It does not rerun verification, generate a long code tour, create `LEARN.md`, or treat a fluent explanation as proof of long-term retention.
