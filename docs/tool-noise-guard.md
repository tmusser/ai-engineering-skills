# Tool Noise Guard

`tool-noise-guard` is an optional passive skill for tool-heavy sessions where verbose
results start consuming attention without adding new information.

It targets **forward propagation**, not runtime history. A Markdown skill cannot erase a
tool payload that the runtime already placed in model context. It can stop that payload
from multiplying through repeated fetches, copied metadata, and verbose summaries.

## The failure mode

A tool returns a useful fact inside a large envelope:

```text
PR #14 is merged at head c1a874a.
```

The envelope may also contain user objects, avatar URLs, duplicated display URLs, null
fields, connector bookkeeping, request timings, session IDs, and unchanged PR metadata.
If the agent repeatedly fetches the same PR, quotes the whole result, and then copies it
into status updates, the useful state becomes a small fraction of the working context.

The guard keeps the operational state instead:

```text
PR #14 | merged | head c1a874a | base main
```

If a later decision needs another field, the agent can re-expand from the original
resource or issue a targeted read.

## What it preserves

Compaction is safe only when the next action remains grounded. Preserve:

- resource anchors needed for follow-up calls
- exact mutation targets, versions, SHAs, paths, and confirmations
- errors and the first actionable traceback or mismatch
- verification results, counts, hashes, and relevant timestamps
- pagination and partial-result state
- changed values and decision-relevant deltas
- provenance needed to reopen or verify the source
- uncertainty, conflict, caveats, and blockers
- fields the user explicitly requested

The skill must not replace evidence with a vague conclusion.

## What it can collapse

Common low-value repetition includes:

- identical wrapper/schema fields across successive responses
- runtime-only connector or session metadata
- transport timing that does not affect the task
- duplicated avatar/profile/display URLs
- repeated null/default fields
- stable descriptive metadata already captured once
- unchanged resource fields that cannot alter the next action

A field is not noise merely because it is verbose. Classification depends on the current
decision.

## Re-fetch discipline

Before repeating a tool call, ask:

> What new information can this call change?

A repeat read is justified when freshness matters, a mutable state could have transitioned,
a mutation needs optimistic-concurrency data, pagination is incomplete, verification needs
new evidence, or the next operation requires a missing field.

A repeat read is not justified merely because the last compact summary feels too small.
Prefer targeted reads and safe batching when the tool supports them.

## Relationship to adjacent skills

| Skill | Compresses / protects | Primary failure mode |
| --- | --- | --- |
| `lean-mode` | user-facing prose | verbose routine responses |
| `tool-noise-guard` | carry-forward tool state | repeated envelopes, metadata, and re-fetches |
| `context-check` | session reasoning state | drift, premise repair, hypothesis sprawl |
| context hydration | startup source selection | loading too much irrelevant repository context |

These can compose. `lean-mode` can keep the response short while `tool-noise-guard` keeps
the underlying tool state dense. `context-check` should still speak only when context risk
itself becomes medium/high.

## Activation

Install it like any other optional skill:

```bash
./install.sh --claude-user --only tool-noise-guard
./install.sh --codex-user --only tool-noise-guard
```

Then explicitly enable it for a tool-heavy task or session:

```text
Use tool-noise-guard passively for this session. Compact repetitive tool metadata,
preserve action anchors and evidence, and do not re-fetch unchanged resources without a
named freshness reason.
```

It should normally produce no user-visible ceremony. The behavior change is the output.

## Limits

This skill does not provide runtime context pruning, KV-cache control, tool-schema
compression, or guaranteed token reduction. Those require support from the agent/runtime
or tool transport layer.

It also must not suppress a necessary read simply because the response is expected to be
large. Correctness, freshness, auditability, and mutation safety outrank token savings.
