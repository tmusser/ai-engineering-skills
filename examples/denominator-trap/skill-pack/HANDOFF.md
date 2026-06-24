# Handoff

## Current status

`mini-spec` froze the metric definition, and Data Trust Pass blocked the
headline metric.

## What is safe to say now

- The current extract is not trustworthy enough for a headline lift estimate.
- Denominator drift, duplicates, synthetic rows, and window inconsistencies are
  present.

## Blocked claims

- performance lift
- causal lift
- revenue impact

## Next recommended task

Rebuild the extract with de-duplicated production rows, one explicit
denominator definition, valid analysis windows, and no leakage field in the
headline metric view.

## Next verification

Re-run Data Trust Pass on the cleaned extract before computing any headline
metric.
