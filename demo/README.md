# Demo

This directory contains a sanitized terminal demo for `ai-engineering-skills`.

The demo uses a fake toy project:

> Build a tiny CLI that reads a CSV file and writes a Markdown summary with row count, column names, missing-value counts, and one example row.

It does not use company names, private paths, real tickets, private repositories, internal architecture, or real data.

## Files

- `sample-data/customers.csv`: fake CSV data for the toy project
- `demo-script.md`: human-readable storyboard
- `demo.tape`: VHS-compatible terminal recording script

## Render

If VHS is installed, run:

```bash
scripts/render_demo.sh
```

The render script writes a GIF from `demo/demo.tape`.

Do not commit generated GIFs unless they are intentionally added later.

## What the demo shows

The tape simulates the workflow without invoking real Claude Code:

1. Install or local setup
2. Claude Code slash commands are available
3. `/mini-spec`
4. `/thin-plan`
5. `/scope-freeze`
6. `/build-one`
7. `/verify-contract`
8. `/handoff`

All working files are created under:

```text
/tmp/ai-engineering-skills-demo
```
