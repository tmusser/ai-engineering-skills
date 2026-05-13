# Small Dashboard POC

## Scenario

Build a dashboard that shows weekly qualified leads by channel for the last eight complete weeks.

## Workflow

1. Use `grill-with-docs-lite` to define "qualified lead", channel attribution,
   refresh cadence, and the exact eight-week date window.
2. Use `mini-spec` to write acceptance criteria: KPI total, weekly grain,
   channel filter, empty-state behavior, and export path.
3. Use `thin-plan` to create slices: fixture data, KPI table, trend chart, filters, verification.
4. Use `scope-freeze` to allow only dashboard code, fixture files, and tests.
5. Use `build-one` to render the KPI table from a fixture before connecting live data.
6. Use `test-mini` to verify row counts, date boundaries, null handling, and one golden KPI total.
7. Use `verify-contract` to record the test command and screenshot or smoke path.
8. Use `ship-mini` before anyone uses the dashboard for planning.

## Concrete checks

- Fixture has two channels, eight complete weeks, one null channel, and one out-of-window row.
- Verification checks row count, total qualified leads, and date range.
- Smoke path opens the dashboard and confirms the KPI table and chart render.
- Ship gate records data freshness, metric deltas, rollback path, and owner notification.
