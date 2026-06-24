# Hero Demo: Messy data work that looks easy until the denominator is wrong

This example is small enough for a terminal GIF or screen recording.

It uses one fake campaign-lift extract and shows two paths:

1. an ungated generic-agent path that computes a confident lift, writes an
   overconfident summary, and passes a shallow public check
2. a skill-pack path that freezes the metric definition, runs Data Trust Pass,
   blocks the headline metric until the claim boundary is clear, records
   evidence, and leaves a resumable handoff

## Files

- `campaign_lift.csv`
- `ungated/`
- `skill-pack/`

## Show it fast

Preview the extract:

```bash
sed -n '1,8p' examples/denominator-trap/campaign_lift.csv
```

Show the ungated path:

```bash
cat examples/denominator-trap/ungated/headline_metric.md
cat examples/denominator-trap/ungated/executive_summary.md
cat examples/denominator-trap/ungated/public_check.md
```

Show the skill-pack path:

```bash
cat examples/denominator-trap/skill-pack/SPEC.md
cat examples/denominator-trap/skill-pack/VERIFY.md
cat examples/denominator-trap/skill-pack/executive_summary.md
cat examples/denominator-trap/skill-pack/HANDOFF.md
```

## What it shows

- auditability
- resumability
- the denominator trap
- public-pass / hidden-fail contrast

## Hidden failures in the extract

- duplicate row
- synthetic/test row
- pre/post date inconsistency
- inconsistent `audience_size` denominator
- leakage-risk column: `future_14d_revenue`

The skill-pack path does not claim to catch every data bug. It shows how a small
workflow can make the failure explicit before a headline metric is shared.
