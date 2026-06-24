# Public Check

Status: `PASS`

Checks:

- `campaign_lift.csv` exists
- required output columns exist
- `headline_metric.md` contains a numeric lift
- `executive_summary.md` exists and is non-empty
- output shape is ready for sharing

What this check does not catch:

- duplicate keys
- synthetic/test rows
- invalid date or window logic
- denominator drift
- leakage-risk fields
