---
name: eco-mode
description: Keep a small, budgeted working context for low-cost model execution without weakening task contracts, required sources, or verification.
---

# Eco Mode

## Purpose

Make bounded agent work economical through source selection, fresh-context
discipline, and a measurable preflight. This is an opt-in working-set policy,
not a second workflow, model switch, or replacement for verification.

## When to use

Use when the operator invokes eco mode, asks to minimize context costs, or runs a
bounded task on a fast inexpensive model. Especially useful for maintenance,
well-scoped coding, extraction, and small-model delegated work.

Do not force it on ambiguous research, incident response, high-stakes decisions,
or tasks whose required evidence cannot fit. Escalate when necessary.

## Inputs

- Objective, current source of truth, scope and acceptance/proof targets
- Only the selected relevant code/docs and durable state files
- Optional provider/model choice outside this skill
- Local selected-content budget, default 60,000 UTF-8 bytes

## Workflow

1. Resolve the route first, or honor an already explicit route. Do not append
   ceremony to a sufficient workflow.
2. Load only the current authority-bearing task sources, relevant file sections,
   and next proof target. Search and expand when a named risk warrants it.
3. Optionally use existing context hydration for Markdown:
   \`python scripts/aes.py context "bounded task" --strict > /tmp/eco.md\`.
   Inspect the packet status and required-file coverage before relying on it.
4. Check the actual selected text files before sending them:
   \`python scripts/aes.py eco /tmp/eco.md\`, or pipe the selected prompt to
   \`python scripts/aes.py eco -\`. The default combined ceiling is 60,000
   bytes; REVIEW_REQUIRED means prune redundancy or explicitly expand.
5. Execute one slice with existing scope controls and verification. Avoid
   redundant tool-output envelopes and needless refetches. Reuse anchors.
6. Preserve required instructions, exact file paths, uncertainties, acceptance
   criteria, failed tests, compatibility checks, and verification evidence.
   Never abbreviate a failing proof into apparent success.
7. On scope drift, missing evidence, or budget pressure, retrieve the smallest
   missing authoritative source. Use a trusted handoff into a fresh context,
   or switch to a more capable model when required. Never silently truncate.
8. Stop after required proof. Measure actual provider token usage and spend
   where available; the byte checker cannot estimate billed usage.

## Model guidance

- Claude Haiku 5.5 (\`claude-haiku-5-5\`) has lower API pricing for prompts up
  to 100k tokens than for prompts above that threshold.
- GPT-6 Luna (\`gpt-6-luna\`) supports \`reasoning.effort: xhigh\` through the
  Responses API. Deeper reasoning may spend more billed output tokens.
- Both models support very large contexts; this mode optimizes cost and
  decision saliency, not merely whether a prompt fits in the window.
- Provider limits, identifiers, tokenizer behavior, and pricing change.
  Check provider documentation before production routing.

## Outputs

No extra ledger by default. On an explicit status request, output only the
selected sources, preflight verdict, preserved proof target, and next action.

The preflight's PASS applies to **selected UTF-8 bytes only**, not full runtime
history, tool schemas, provider tokens, or pricing. It never removes context
already injected into a live session.

## Stop conditions

- Required sources are represented or the escalation is explicit.
- Context preflight was inspected and verification remains intact.
- No redundant summary cycle was created solely for token savings.

## Anti-patterns

- Assuming a 1M context window means all tokens are cheaply priced.
- Treating 60,000 bytes as 60,000 model tokens or a guaranteed cost tier.
- Loading all installed skills or the full repository by default.
- Dropping risk, permission constraints, or verification to fit a budget.
- Pretending a summary erased previously supplied context.
- Silently truncating required files, reclassifying unknowns as irrelevant,
  or keeping a cheap model on a task beyond its reliable capabilities.
