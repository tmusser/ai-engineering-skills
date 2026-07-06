# Skill Map

Use this repo as a small operating loop for bounded AI-assisted technical work.

## Routing map

```mermaid
flowchart TD
  A["Pre-flight<br/>ceremony-budget"] --> B["Clarify<br/>grill-with-docs-lite<br/>constitution-lite"]
  A --> C["Specify<br/>mini-spec<br/>checklist-mini"]
  A --> D["Constrain<br/>scope-freeze"]
  B --> C
  C --> E["Plan<br/>thin-plan<br/>analyze-mini"]
  E --> D
  D --> F["Build<br/>build-one"]
  F --> G["Verify<br/>test-mini<br/>verify-contract"]
  G --> H["Ship<br/>ship-mini"]
  H --> I["Handoff<br/>handoff"]
  J["Diagnose<br/>diagnose-loop<br/>bug-capture"] --> D
  J --> G
```

`ceremony-budget` is an optional pre-flight router. Use it to choose the smallest
safe path before selecting clarify, specify, plan, build, verify, ship, or
handoff skills.

## Context-pressure control layer

- `scope-freeze` limits blast radius before work.
- `verify-contract` records evidence after work.
- `context-check` detects drift during work.
- `handoff` preserves durable state between sessions.

Together they support bounded execution and verifiable progress.

## Failure mode diagram

```mermaid
flowchart TD
  A["Vague request"] --> B["Many edits"]
  B --> C["Weak verification"]
  C --> D["Long context"]
  D --> E["Lost saliency"]
  E --> F["Buggy / bloated output"]

  G["Clarified request"] --> H["mini-spec"]
  H --> I["One vertical slice"]
  I --> J["scope-freeze"]
  J --> K["build-one"]
  K --> L["verify-contract"]
  L --> M["handoff"]
  M --> N["fresh context"]
```

## Workflow recipes

See [docs/recipes.md](recipes.md) for small-project, debug, ML/dashboard, analytical,
and cross-functional recipes.

For scheduled or delegated tool-using runs, see
[docs/agent-worker-safety.md](agent-worker-safety.md) before giving a workflow write
access.
