---
name: context-check
description: Detect context drift, rehydration loops, hypothesis sprawl, scope creep, active-mode loss, and durable-state gaps. Recommend the smallest corrective action.
---

# Context Check

## Purpose

Keep sessions cheap, bounded, and durable. Detect distortion early and recommend minimal correction.

## When to use

Passive guardrail. Speak **only** on medium/high risk (or when explicitly invoked).

Low risk: stay silent **unless explicitly invoked**. If explicitly invoked on low risk, output one line: `CONTEXT RISK: low — continue.`

Trigger on repeated facts, scope/hypothesis changes, multiple debug hypotheses, handoff pressure, or active modes that may need to persist.

## Inputs

- Current conversation
- Durable state files if present
- Current task, phase, loop, and active modes if known
- Current debugging hypothesis if debugging

## Workflow

1. Scan for risk signals (repeated premises, history restatement, scope drift, hypothesis sprawl, weak durable state, active-mode loss).
2. Assign risk: low / medium / high.
3. Recommend exactly one best move. For medium/high risk, prefer: scope-freeze | update durable state | handoff | diagnose-loop | restart. Use `continue` only for explicit low-risk checks.
4. On medium/high risk, output the structured block. Recommend restart only when context is actively corrupting decisions.

**Output format (medium/high only):**

```text
CONTEXT RISK: medium
TRIGGER: repeated premise repair on X
BEST MOVE: handoff | scope-freeze | update PLAN.md | etc.
FREEZE NOW: [key facts/decisions/modes/hypothesis]
NEXT ACTION: ...
```

Keep FREEZE NOW limited to facts, decisions, assumptions, IDs, files, tests, active modes, current hypothesis, and next verification that must survive.

## Outputs

- Concise risk assessment
- One recommended action
- Minimal freeze list when needed

## Success looks like

- Low risk → no output (unless explicitly invoked), work continues cleanly.
- Medium risk → quick state update prevents drift.
- High risk → handoff or restart before more damage.

**Example (medium risk):**

```text
CONTEXT RISK: medium
TRIGGER: scope subtly expanding
BEST MOVE: scope-freeze
FREEZE NOW: only modify files in /src/featureX
```

## Stop conditions

- Next action is clear.
- Durable state holds necessary facts.
- One active hypothesis (if debugging).
- Active modes captured for persistence.

## Anti-patterns

- Triggering on normal long conversations.
- Producing checklists instead of one action.
- Full thread summaries.
- Letting multiple debug hypotheses coexist.
- Assuming modes survive without writing them down.
