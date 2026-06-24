# Spec

## Objective

Decide whether this extract is trustworthy enough to support a headline
campaign-lift statement.

## Metric definition

- Grain: one de-duplicated production row per `arm x phase x segment x analysis window`
- Numerator: `orders_7d` from production rows only
- Denominator: de-duplicated `audience_size` for the same grain
- Window: `event_date` must fall inside `analysis_window_start` to
  `analysis_window_end`
- Exclusions: duplicate rows, `is_test_row=true`, rows outside window, and
  leakage fields from the headline metric
- Claim boundary: no causal or performance claim until denominator, duplicate,
  synthetic/test, and window checks pass

## Acceptance criteria

- No headline lift is shared until the denominator and row-quality checks pass.
- Leakage-risk fields are excluded from the headline metric.
- Allowed claims and blocked claims are recorded before an executive summary is
  drafted.
