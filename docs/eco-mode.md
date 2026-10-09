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

## Current model rationale (October 9, 2026)

| Model | Relevant detail | Tactic |
| --- | --- | --- |
| Claude Haiku 5.5 | 1M context. API prompts up to 100k tokens cost $0.10 input / $0.50 output per million; above 100k cost $0.50 / $2.50. | Keep the full provider-counted input below the price boundary. |
| GPT-6 Luna | ~1.05M context; \`reasoning.effort: xhigh\` is supported in the Responses API. | Reserve deeper reasoning for bounded tasks that benefit; measure billed output/reasoning. |

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
