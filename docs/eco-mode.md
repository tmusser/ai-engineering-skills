# Eco Mode

Eco mode is an optional small-working-set policy, not a new workflow stage or
automatic model router. It combines route-first context loading, selective
hydration, short tool-result digests, and existing verification and handoff.

## Install and use

From the repository checkout:

~~~bash
./install.sh --claude-user --only eco-mode
# Or:
./install.sh --codex-user --only eco-mode
~~~

Ask: "Use eco-mode for this bounded fix; retain scope, source authority, and
verification. Escalate instead of losing required evidence."

For an explicitly selected Markdown context packet:

~~~bash
python scripts/aes.py context "fix export behavior" \
  --require-file SPEC.md --strict > /tmp/eco.md
python scripts/aes.py eco /tmp/eco.md
~~~

Or check manually selected files or stdin:

~~~bash
python scripts/aes.py eco SPEC.md HANDOFF.md --max-bytes 60000
python scripts/aes.py eco --format json - < /tmp/selected-prompt.txt
~~~

The helper counts the **combined UTF-8 bytes** in the selected files, default
ceiling 60,000. It emits PASS (exit 0), REVIEW_REQUIRED (exit 3) or input error
(exit 2). It never truncates, sends provider requests, or changes models.

**This does not measure the full prompt or price.** Agent/system instructions,
tool schemas, earlier context, cached material, non-text inputs, and provider
tokenization are outside this local check. Provider-reported input/output tokens,
reasoning usage, caching and cost are the real measurement. PASS does not mean
the provider's cheap pricing tier is guaranteed.

## Context sufficiency (optional)

A small context can still omit a source needed for the next decision. Opt in to
explicit requirements when a task has named authoritative inputs or proof targets:

~~~bash
python scripts/aes.py eco SPEC.md VERIFY.md \
  --require-source SPEC.md \
  --require-source VERIFY.md \
  --require-proof "python -m pytest tests/test_export.py"
~~~

For an existing generated Markdown context packet, use its *actual filename*
along with the root containing its source files:

~~~bash
python scripts/aes.py eco /tmp/eco.md --root /path/to/project \
  --require-source SPEC.md --require-proof "tests/test_export.py"
~~~

- `--require-source` is repeatable and accepts normalized repository-relative
  paths. It requires a directly selected source file or a real excerpt verified
  against its current source content, line range, and hash. A filename in a
  metadata table or omitted-candidate list is **not** sufficient.
- `--require-proof` is repeatable and checks a literal phrase in selected
  content or a source-verified packet excerpt. Name the intended acceptance
  or verification anchor yourself; the tool cannot infer which proof matters.
- `--root` identifies the project for checking source paths and packet
  freshness (defaults to the working directory).
- Missing requirements or stale/unsafe packet excerpts return
  `REVIEW_REQUIRED` (exit 3). Invalid source paths return input error (exit 2).
  Existing byte-only behavior is unchanged if no requirement flags are used.
- A PASS proves **textual representation, not semantic sufficiency**.
  It does not execute a test, judge evidence quality, discover missing
  requirements, guarantee correct agent behavior, or estimate API costs.
  If context is inadequate despite a PASS, load more authoritative context.

## Section-aware sufficiency (optional)

A verified excerpt from `SPEC.md` can show the objective while omitting the
acceptance criteria. Requiring the source file alone does **not** establish
that the governing section is present.

Use the repeatable `--require-heading FILE::Heading` check to require the
entire named Markdown section (including nested subheadings):

~~~bash
python scripts/aes.py eco /tmp/eco.md --root /path/to/project \
  --require-heading "SPEC.md::Acceptance criteria" \
  --require-heading "SPEC.md::Invalid if"
~~~

A directly selected whole source satisfies its existing unique heading.
For a generated context packet, one current-source-verified excerpt must
contain the **complete** ATX heading section. Source metadata, a heading
title alone, and partial or stale excerpts are not sufficient.

Missing, partial, or ambiguous headings produce `REVIEW_REQUIRED` (exit 3);
malformed `FILE::Heading` requirements and unsafe paths are input errors (2).
A PASS means the named section was represented, not that it is adequate,
correct, or sufficient for the agent's task. Choose governing headings
explicitly; the tool cannot infer relevance.

This option composes with `--require-source`, `--require-proof`, and
the existing byte ceiling; without it, prior behavior is unchanged.

## Current model rationale (October 9, 2026)

| Model | Relevant detail | Tactic |
| --- | --- | --- |
| Claude Haiku 5.5 | 1M context. API prompts up to 100k tokens cost $0.10 input / $0.50 output per million; above 100k cost $0.50 / $2.50. | Keep the full provider-counted input below the price boundary. |
| GPT-6 Luna | ~1.05M context; `reasoning.effort: xhigh` is supported in the Responses API. | Reserve deeper reasoning for bounded tasks that benefit; measure billed output/reasoning. |

Both models have large *capacity*; eco mode targets *economical execution*.
60k selected bytes is a conservative local ceiling, not a universal safe
100k-token bound for the complete API request. Pricing and limits may change:
consult [Anthropic's model docs](https://platform.claude.com/docs/en/models/haiku-5-5/overview)
and [OpenAI's model docs](https://developers.openai.com/api/docs/models/gpt-6-luna).

## Preservation and escalation

- Keep scope, acceptance criteria, exact source anchors, risks, and required
  verification. Inspect context-pack WARN/FAIL and never silently omit sources.
- Drop redundant history first; use targeted reads for newly necessary files.
- If a required source does not fit, raise the local ceiling with an explicit
  reason, use a stronger model, or move to a fresh session with trusted HANDOFF.md.
- A summary cannot erase tokens already present in a live session.
- Capture actual provider usage and verified outcomes for an A/B comparison
  before claiming dollar savings or parity with a higher-cost model.

This mode complements [context isolation](context-isolation.md),
[context hydration](context-hydration.md), and the existing proof gates.
