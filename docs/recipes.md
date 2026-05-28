# Workflow Recipes

Use the smallest workflow that fits the task. These recipes show common routes through the skills.

## Level 0 — Patch

Use for tiny reversible edits that only need one sanity check.

```mermaid
flowchart TD
  A[Tiny reversible edit] --> B[Run one sanity check]
  B --> C[Record verification in commit message]
```

## Level 1 — Micro behavior change

Use for small bounded behavior changes that still fit in one slice.

```mermaid
flowchart TD
  A[Inline scope-freeze] --> B[Build one]
  B --> C{Behavior changed?}
  C -- Yes --> D[Test mini]
  C -- No --> E[Verify contract]
  D --> E
```

## Cross-functional infrastructure coordination

Use when a project spans multiple teams, external owners, tickets, meetings, credentials, platform details, or unresolved technical access questions.

```text
grill-with-docs-lite
→ external context lookup
→ CONTEXT.md
→ TODO.md
→ stakeholder ask files
→ verification scripts
→ private context packs
```

```mermaid
flowchart TD
  A["Meeting transcript<br/>or brain dump"] --> B["grill-with-docs-lite"]
  B --> C["CONTEXT.md<br/>project source of truth"]

  C --> D["External context lookup"]
  D --> D1["Drive / docs"]
  D --> D2["Slack / chat history"]
  D --> D3["Jira / tickets"]
  D --> D4["Vendor docs / WebFetch"]

  D1 --> E["Distilled facts"]
  D2 --> E
  D3 --> E
  D4 --> E

  E --> F["TODO.md<br/>daily driver"]
  E --> G["stakeholder/asks.md<br/>accountability"]
  E --> H[".local/context/warehouse-context.md<br/>private technical context"]
  E --> I["verify_feature.py<br/>smoke test"]

  F --> J["Manager-ready status"]
  G --> J
  H --> J
  I --> J
```

Use `.local/` for private technical context and keep it gitignored.

## Analytical deliverable / scenario memo

Use for opportunity sizing, scenario analysis, stakeholder memos, SQL → CSV → Python → Markdown analysis, or a transcript or meeting request that needs a structured deliverable.

```mermaid
flowchart TD
  A["Private request or transcript<br/>(not committed)"] --> B["grill-with-docs-lite"]
  B --> C["CONTEXT.md<br/>distilled requirements"]
  C --> D["mini-spec"]
  D --> E["SPEC.md<br/>formula, assumptions, acceptance criteria"]
  E --> F["checklist-mini"]
  F --> G{"Ready with<br/>documented assumptions?"}
  G -- "No" --> H["Resolve blockers<br/>or mark NEEDS CLARIFICATION"]
  H --> D
  G -- "Yes" --> I["thin-plan"]
  I --> J["Vertical slices<br/>inputs → scenario table → narrative → deliverable"]
  J --> K["build-one × slices"]
  K --> L["test-mini"]
  L --> M["Deterministic checks<br/>SQL sanity, math assertions,<br/>framing/banned-word checks"]
  M --> N["Stakeholder-ready<br/>scenario memo or table"]

  N --> O{"Does proof need to<br/>be durable?"}
  O -- "Yes" --> P["verify-contract"]
  O -- "No" --> Q{"Will it become<br/>source-of-truth?"}

  P --> Q
  Q -- "Yes" --> R["ship-mini"]
  Q -- "No" --> S{"Will another session<br/>continue?"}

  R --> S
  S -- "Yes" --> T["handoff"]
  S -- "No" --> U["Done"]
```

```text
grill-with-docs-lite
→ mini-spec
→ checklist-mini
→ thin-plan
→ build-one × slices
→ test-mini
```

Optional gates:

- Use `scope-freeze` if working inside an existing repo with shared modules, configs, or broad blast radius.
- Use `verify-contract` if the proof needs to become a durable audit artifact.
- Use `ship-mini` if the output will be committed, reused, scheduled, automated, published, or treated as a source of truth.
- Use `handoff` only if another session or agent will continue.

Deterministic checks can include SQL row and count sanity checks, exact arithmetic checks, banned-word or framing checks, scenario table assertions, and methodology bridge checks between different metric definitions.

## When to skip steps

- Skip `mini-spec` when the change is mechanical, single-purpose, and unambiguous.
- Skip `thin-plan` when there is only one slice.
- Skip `scope-freeze` when the workspace is already isolated and the blast radius is obvious.
- Use test-mini for correctness checks; use verify-contract when the verification evidence itself needs to be durable.
- Skip `test-mini` only when no behavior changed or when a runnable test is not practical; use a smoke path instead.
- Use `ship-mini` when the output becomes a committed, shared, scheduled, automated, published, or source-of-truth artifact.
- Skip `ship-mini` only when the output is not user-facing, scheduled, autonomous, decision-impacting, or data-sensitive.
- Use `handoff` for continuation, not completion.
- Do not skip `verify-contract` when behavior changed.

## Spike / scratchpad

Use a spike to test an idea quickly.

- Do not create `SPEC.md` or `PLAN.md`.
- Keep it in one scratch file when possible.
- Use fake or toy data.
- When the spike grows beyond its boundary, stop and promote it to Level 2 by creating `mini-spec`, `verify-contract`, and `handoff` artifacts.

## Default small-project flow

Use when a small project needs enough structure to ship safely.

```mermaid
flowchart TD
  A["grill-with-docs-lite"] --> B["mini-spec"]
  B --> C["checklist-mini"]
  C --> D["thin-plan"]
  D --> E["scope-freeze"]
  E --> F["analyze-mini"]
  F --> G["build-one"]
  G --> H["test-mini"]
  H --> I["verify-contract"]
  I --> J{"User-facing, scheduled, autonomous, or decision-impacting?"}
  J -- "Yes" --> K["ship-mini"]
  J -- "No" --> L["handoff"]
  K --> L
```

## Debug / bugfix flow

Use when behavior is failing and feature work should pause.

```mermaid
flowchart TD
  A["diagnose-loop"] --> B["bug-capture"]
  B --> C["scope-freeze"]
  C --> D["build-one"]
  D --> E["test-mini"]
  E --> F["verify-contract"]
  F --> G{"Needs ship gate?"}
  G -- "Yes" --> H["ship-mini"]
  G -- "No" --> I["handoff"]
  H --> I
```

## Fresh-context development loop

Use when long context is starting to drift or another session will continue.

```mermaid
flowchart TD
  A["Pick one vertical slice"] --> B["scope-freeze"]
  B --> C["build-one"]
  C --> D["test-mini"]
  D --> E["verify-contract"]
  E --> F["handoff"]
  F --> G["Fresh context"]
  G --> H["Confirm next task and verification"]
  H --> I["Next slice"]
  I --> B
```

## ML / dashboard workflow

Use when outputs may influence analysis, metrics, model decisions, or stakeholder review.

```mermaid
flowchart TD
  A["mini-spec"] --> B["checklist-mini"]
  B --> C["thin-plan"]
  C --> D["test-mini"]
  D --> E["verify-contract"]
  E --> F["ship-mini"]
  F --> G["handoff"]
```

Check fixture data, row counts, null checks, metric deltas, and screenshot or smoke verification.

## Agent worker workflow

Use when an agent will read queues, boards, tickets, files, or tools and take bounded action.

```mermaid
flowchart TD
  A["constitution-lite"] --> B["grill-with-docs-lite"]
  B --> C["mini-spec"]
  C --> D["scope-freeze"]
  D --> E["build-one"]
  E --> F["test-mini"]
  F --> G["ship-mini"]
  G --> H["handoff"]
```

Define autonomy level, allowed tools, forbidden actions, rollback, and logs.
