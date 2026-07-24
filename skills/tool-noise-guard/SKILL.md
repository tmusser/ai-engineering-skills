---
name: tool-noise-guard
description: Passive guardrail that compacts repetitive tool-result envelopes, preserves decision-relevant anchors and deltas, and suppresses redundant re-fetches without pretending prior context disappeared.
---

# Tool Noise Guard

## Purpose

Reduce the forward propagation of tool-call bloat during tool-heavy work.

**Compact forward, not backward.** This skill cannot remove raw tool output that the
runtime already injected into context. It prevents that cost from multiplying by
re-quoting, re-summarizing, and re-fetching the same low-value metadata on later turns.

Never trade required evidence for token savings.

## When to use

Optional passive guardrail. Once explicitly enabled for a tool-heavy task or session,
stay active until the user disables it or the task no longer uses tools.

Stay silent by default. Intervene behaviorally when one or more of these signals appear:

- successive tool results repeat the same wrapper, schema, or stable metadata
- a list/search response contains many fields but only a few affect the next decision
- the same resource is fetched or polled again without a concrete freshness reason
- a follow-up call can reuse an existing ID, cursor, path, or resource reference
- verbose tool envelopes are being copied into summaries, handoffs, or user-facing prose

Do not compact aggressively when exact raw payload shape is itself the evidence, when
results conflict, when an error is not yet understood, or when a mutation/audit step
requires exact confirmation.

## Inputs

- Current task and next decision
- Recent tool calls and results
- Resource identifiers, paths, cursors, commit SHAs, line references, and timestamps
- Current mutation, verification, pagination, or freshness state
- Any exact fields required by the next tool call

## Workflow

1. Before repeating a tool call, ask: **what new information can this call change?**
2. Reuse already-known resource anchors instead of rediscovering the same object.
3. For repeated result shapes, classify fields into:
   - `anchor` — needed to identify, reopen, mutate, cite, paginate, or verify the resource
   - `delta` — changed since the previous relevant result
   - `evidence` — affects correctness, status, risk, or the next decision
   - `noise` — repeated wrapper or metadata with no current operational use
4. Carry `anchor + delta + evidence` forward. Do not restate `noise`.
5. Prefer a targeted follow-up operation over rehydrating a full resource when both answer
   the same question.
6. If polling mutable state, poll only when a state transition can change the next action.
   Do not immediately repeat an unchanged status call for reassurance.
7. When several equivalent reads are needed, prefer a safe batch/list operation when the
   tool supports one and batching does not widen scope or hide per-item failures.
8. If compacting a result cluster, retain a minimal working digest rather than another
   prose summary.
9. Re-expand from the original tool/resource only when the next decision genuinely needs
   a field that was not retained.

### Minimal working digest

Use this shape internally or in a handoff only when it helps continuation:

```text
TOOL STATE
Source/action: GitHub PR lookup
Anchors: PR #14, head=c1a874a, base=main
Delta: open/draft -> merged
Evidence: merged_at=2026-07-24T23:20:14Z
Next freshness condition: only re-fetch if merge state or head SHA matters again
```

Do not create a `TOOL_STATE.md` ledger merely to prove compaction happened.

### Always preserve

Never compact away a field that is still needed for:

- a follow-up tool call: IDs, cursors, paths, refs, resource handles
- mutation safety: exact target, expected version/SHA, confirmation, failure reason
- verification: command/result, pass/fail state, counts, hashes, relevant timestamps
- debugging: first actionable error, traceback/mismatch details, failing input
- provenance: source, file/line reference, issue/PR/run number, commit SHA when relevant
- completeness: pagination state, omitted-result warning, partial-success state
- judgment: uncertainty, conflict, caveat, blocker, or changed value
- user intent: any field the user explicitly asked to see

### Safe noise candidates

Compact these only when they are stable and not operationally relevant:

- repeated schema keys and unchanged wrapper fields
- connector/session IDs used only by the runtime
- request latency and transport bookkeeping
- duplicate avatar/profile/display URLs
- repeated null/default fields
- repeated labels or descriptions already captured once
- unchanged resource metadata that does not affect freshness or the next action

Similarity is not identity. If two values differ, do not collapse them until the
difference is classified as irrelevant to the current decision.

## Outputs

Normally no user-visible output. The effect should be fewer redundant tool calls and
smaller carry-forward summaries.

When explicitly invoked for a status check, use at most:

```text
TOOL NOISE: medium
COMPACT: repeated PR envelope -> PR number, head SHA, state, changed fields
SKIP: immediate unchanged-status re-fetch
PRESERVE: mutation target + CI status + error evidence
```

## Stop conditions

- The next action can be taken without re-reading a verbose prior envelope.
- Required anchors, deltas, evidence, uncertainty, and pagination state remain available.
- No repeated tool call exists only for reassurance or metadata rediscovery.
- Any future re-fetch has a named freshness, mutation, verification, or missing-field reason.

## Anti-patterns

- Claiming that compaction removed tokens already present in runtime context.
- Replacing exact verification evidence with "looks good" or "pass".
- Dropping IDs, cursors, SHAs, paths, or error details needed for the next operation.
- Collapsing similar-but-different results without checking the difference.
- Treating mutable data as permanently cached.
- Suppressing a necessary tool call merely to save tokens.
- Re-fetching the same full object because its compact digest feels too short.
- Creating a durable compaction artifact for routine tool traffic.
- Echoing runtime bookkeeping into user-facing updates when it has no decision value.
