# Workflow Doctor

`scripts/workflow_doctor.py` provides a read-only diagnosis of current workflow
state.

It answers three narrow questions:

- Which durable artifacts are present and usable?
- Do recorded verification and live deterministic checks agree?
- What is the single safest next move supported by the current evidence?

The doctor is not a workflow engine. It does not infer task intent, select skills,
write artifacts, repair state, or call an LLM.

## Recommended command

Run from the repository root with an explicit comparison base:

```bash
python scripts/workflow_doctor.py --base origin/main
```

Machine-readable output is available for CI or local tooling:

```bash
python scripts/workflow_doctor.py --base origin/main --format json
```

Custom artifact paths are supported:

```bash
python scripts/workflow_doctor.py \
  --base main \
  --spec artifacts/SPEC.md \
  --scope artifacts/SCOPE.md \
  --verify artifacts/VERIFY.md \
  --handoff artifacts/HANDOFF.md
```

## What it inspects

The doctor reports:

- current branch, commit, and clean or dirty working-tree state;
- whether `SPEC.md` has a meaningful Objective and Acceptance criteria;
- whether optional `SCOPE.md` contains the canonical scope-freeze boundary;
- the status recorded in `VERIFY.md`;
- the result of `scripts/verify_gate.py` when `--base` is supplied;
- freshness of an existing `HANDOFF.md` through the bundled handoff guard;
- changed files reported by the deterministic verify gate;
- exactly one next move.

`SCOPE.md` and `HANDOFF.md` remain optional. Their absence does not add ceremony or
downgrade otherwise green evidence. When either artifact exists, the doctor refuses
to silently trust an incomplete scope or stale continuation state.

## Status semantics

- `PASS` — the spec is actionable, recorded verification is `PASS`, the
  deterministic gate is `PASS`, and any existing scope or handoff is usable.
- `FAIL` — recorded or deterministic verification reports a functional or contract
  failure.
- `REVIEW_REQUIRED` — required evidence is missing or incomplete, the deterministic
  gate was not established, an existing scope is incomplete, a handoff is stale or
  uncheckable, or Git state cannot be inspected safely.

Exit codes are `0` for `PASS`, `1` for `FAIL`, and `2` for `REVIEW_REQUIRED`.

## Decision precedence

The next move is selected conservatively:

1. establish or complete the task contract;
2. reconcile an existing incomplete scope freeze;
3. fix verification failures;
4. record missing verification evidence;
5. resolve deterministic or recorded review-required items;
6. regenerate stale continuation state;
7. trust a handoff's next task only after freshness returns `PASS`;
8. otherwise proceed only with the next user-approved action.

A stale handoff never gets to nominate the next task. A recorded `PASS` never
outranks a failing or unestablished deterministic gate.

## Read-only boundary

The doctor runs only read operations and existing read-only checks. It writes no
Markdown, modifies no Git state, and exposes no GitHub write path. Text and JSON are
printed to standard output only.

## Claim boundary

A green doctor result means the available workflow artifacts and deterministic
checks are internally consistent under these rules. It does not prove that the
specification is correct, the tests are sufficient, or the implementation is free
of defects. Human judgment still owns task classification and the decision to take
the reported next action.
