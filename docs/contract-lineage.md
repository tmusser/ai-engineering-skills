# Contract lineage checker

`scripts/check_contract_lineage.py` verifies the optional execution-contract identity
across durable workflow artifacts.

It is intentionally inactive when a task does not use a contract ID. Tiny or reversible
work remains valid without identity metadata.

## What it checks

When `SPEC.md` declares an active `Contract ID`, the checker:

- treats that SPEC ID as the active contract;
- verifies any existing `PLAN.md`, `VERIFY.md`, and `HANDOFF.md` carry the same ID;
- rejects downstream artifacts that still point at the parent/superseded contract;
- rejects unrelated or multiple contract IDs in one artifact;
- rejects a contract that names itself as its parent;
- requires a meaningful replan reason when a parent contract is recorded;
- checks that the recorded base commit resolves and is an ancestor of the current `HEAD`.

The base check establishes local Git provenance only. It does not prove that the chosen
base was the semantically correct authorization point.

## What it does not check

The checker does not:

- require contract IDs for ordinary work;
- invent IDs or rewrite artifacts;
- reconstruct historical SPEC files from Git history;
- cryptographically authenticate a contract;
- infer whether the task stayed inside behavioral or file scope;
- replace `scope_gate.py`, `verify_gate.py`, handoff freshness, or human review;
- install hooks or intercept agent/runtime events.

## Status semantics

### PASS

`PASS` means either:

- no contract identity is active, so lineage enforcement is intentionally inactive; or
- an active contract is present and all existing downstream durable artifacts identify
  that same contract, with locally establishable base provenance.

### FAIL

`FAIL` is reserved for clear lineage contradictions:

- multiple active IDs;
- self-parenting;
- a downstream artifact naming a different contract;
- a downstream artifact naming the known parent/superseded contract.

### REVIEW_REQUIRED

`REVIEW_REQUIRED` means lineage cannot be established cleanly, for example:

- a downstream artifact exists but omits the active contract ID;
- a downstream artifact declares an ID while SPEC has none;
- a parent exists without a meaningful replan reason;
- the base commit is missing, `unknown`, unavailable, or not an ancestor of current
  `HEAD`.

## Usage

```bash
python scripts/check_contract_lineage.py
python scripts/check_contract_lineage.py --format json
```

Custom artifact locations are supported:

```bash
python scripts/check_contract_lineage.py \
  --spec state/SPEC.md \
  --plan state/PLAN.md \
  --verify state/VERIFY.md \
  --handoff state/HANDOFF.md
```

The unified CLI exposes the same checker without changing its arguments or exit codes:

```bash
python scripts/aes.py lineage --format json
```

Exit codes follow the repository's deterministic status convention:

- `0` — `PASS`;
- `1` — `FAIL`;
- `2` — `REVIEW_REQUIRED`.

## Replan example

```text
# SPEC.md
Contract ID: task-export-02 | Parent: task-export-01 | Base commit: 4f2a91c
Replan reason: existing CLI compatibility seam changed the accepted slice
```

Every downstream durable artifact created for that active task should then carry:

```text
Contract ID: task-export-02
```

A `VERIFY.md` or `HANDOFF.md` that still names `task-export-01` is not merely stale
formatting; it is evidence from an obsolete contract generation and the checker returns
`FAIL`.

## Design boundary

Contract identity remains optional. The invariant is:

> No ID, no lineage ceremony. Once a SPEC opts in, durable downstream artifacts must not
> silently mix contract generations.

This keeps the feature useful for delegated, replanned, or multi-session work without
turning every patch into a formal contract system.
