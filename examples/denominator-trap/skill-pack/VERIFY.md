# Verify

## Verification

- Artifact reviewed: `campaign_lift.csv`
- Method: Data Trust Pass before any headline lift claim
- Headline metric status: blocked

## Data Trust

- Denominator check: `FAIL`
  Treatment post `audience_size` values drift across rows: `1200`, `1200`,
  `900`, `75`.
- Duplicate check: `FAIL`
  `row_id=2` appears twice.
- Synthetic/test check: `FAIL`
  `row_id=4` has `is_test_row=true`.
- Date/window check: `FAIL`
  `row_id=5` is marked `phase=pre`, carries the post window
  `2026-03-15..2026-03-28`, and has `event_date=2026-03-10` outside that
  window.
- Leakage check: `BLOCKED`
  `future_14d_revenue` exists and is not allowed in a headline lift claim.
- Assignment balance: `WEAK`
  Control post audience is `300` while treatment post rows total `3375` before
  cleanup.
- Sample size: `WEAK`
  Only one control post row is present.
- Claim language: `BLOCKED`
  No "caused", "proved", or headline "lift" claim should be shared from this
  extract.

## Allowed claims

- The current extract is not trustworthy enough for a headline lift estimate.
- The denominator drifts across treatment post rows.
- Duplicate, synthetic, and out-of-window rows must be removed before analysis.

## Blocked claims

- The campaign caused lift.
- The treatment beat baseline.
- The extract proves revenue impact.
