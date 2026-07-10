# Ceremony Budget

Ceremony budget exists to keep this repo honest.

Good agent process is not "always write more artifacts." Good agent process knows
when an artifact buys back more attention or safety than it costs.

This repo should know when not to use itself.

## Rule

Spend ceremony only when it buys back attention or safety.

That means:

- reduce ambiguity before it becomes a wrong implementation
- stop scope drift before it becomes unrelated edits
- strengthen verification before weak proof is mistaken for done
- preserve context before the real constraint gets lost
- leave resume state before a fresh session has to re-derive the work
- add gates before irreversible or decision-impacting changes

If the next artifact does not do one of those jobs, skip it.

## What ceremony budget outputs

Usually no additional block is needed when the task or wrapper already supplies
an explicit route. Otherwise use this short routing block:

```text
CEREMONY ROUTE
Level: 0 | 1 | 2 | 3
Next action: ...
Use: ...
Skip: ...
Proof and stop: ...
```

The route replaces a larger default workflow. It must not append a second process
contract, restate a wrapper, invoke skills merely because they exist, or require a
budget ledger. Do not create `CEREMONY_BUDGET.md` by default.

## Levels

### Level 0

Tiny reversible patch.

- Use: direct patch plus one sanity check
- Typical skips: `mini-spec`, `thin-plan`, `handoff`
- Proof and stop: one command passes, then stop

### Level 1

One bounded slice with low ambiguity but enough behavior change to justify an
explicit boundary and proof.

- Use: `inline boundary -> build-one -> targeted verify -> stop`
- Typical skips: `scope-freeze` artifact, `mini-spec`, `thin-plan`, `handoff`
- Proof and stop: targeted verification passes and no named risk remains

### Level 2

Small vertical slice with real ambiguity, moderate scope pressure, or a genuine
risk that weak proof will be mistaken for done.

- Use: `compact mini-spec -> build-one -> targeted test -> verify-contract -> stop`
- Typical skips: `thin-plan`, `scope-freeze` artifact, `checklist-mini`, `analyze-mini`, `ship-mini`
- Proof and stop: acceptance criteria and deterministic proof pass; use `handoff` only for real continuation risk

### Level 3

User-facing, scheduled, autonomous, decision-impacting, data-sensitive, risky, or
multi-slice work.

- Use: `grill-with-docs-lite -> mini-spec -> checklist-mini -> thin-plan -> scope-freeze -> analyze-mini -> build-one -> test-mini -> verify-contract -> ship-mini -> handoff`
- Typical skips: only skills that clearly do not apply
- Proof and stop: durable verification and guardrails pass; stop at the next gate

## Compatibility reserve

For each named preserved behavior, non-goal, or adjacent compatibility seam,
reserve the cheapest relevant negative or regression check when one is available.

Light routing may omit planning artifacts, but it must not omit a cheap check that
protects explicitly preserved behavior. This is focused proof, not a reason by
itself to choose a heavier workflow.

## Escalation triggers

Escalate when:

- ambiguity blocks implementation
- scope starts drifting past the intended slice
- verification is too weak to support the claim of done
- context is long enough that key constraints may be lost
- another session must resume safely
- compatibility seams, test meaning, or data semantics may break silently
- the change is hard to undo or affects decisions, users, or public behavior

## De-escalation triggers

De-escalate when:

- the task is still a tiny reversible edit
- the next artifact would only restate what is already explicit
- one shorter proof path covers the same risk
- a larger route was chosen out of habit rather than because the task needs it
- the strongest remaining risk has already been addressed by the current route

## Resume and verify-before-edit stop rules

Stop and verify before editing when:

- the request is still ambiguous
- compatibility seams are unclear
- existing tests may lose meaning
- data or fixtures may be changed without an explicit boundary
- the next step would create broad writes without a proof target

Stop and resume later when:

- another session can continue more safely from a verified state than from a
  longer live thread
- the current session is carrying too much context to reason cleanly
- the routing decision has changed and the next safer move is to hand off

## Examples

### Already-prescriptive wrapper

```text
Route already explicit.
Missing guard: stop immediately after verification and required proof pass.
Next action: implement the named seam.
```

No second ceremony block, durable routing artifact, or budget ledger is needed.

### Tiny reversible patch

```text
Level: 0
Next action: fix the README typo
Use: direct patch -> markdownlint
Skip: mini-spec, ledger, handoff
Proof and stop: clean lint result, then stop
```

### Small bounded feature

```text
Level: 1
Next action: add the bounded parser branch
Use: inline boundary -> build-one -> targeted test
Skip: mini-spec, ledger, handoff
Proof and stop: parser test passes, then stop
```

Implementation starts immediately; no ledger is created. If the task explicitly
names preserved parser behavior, add the cheapest relevant regression check before
stopping.

### Small feature with real ambiguity

```text
Level: 2
Next action: define the compact export acceptance block
Use: compact mini-spec -> build-one -> targeted test -> verify-contract
Skip: thin-plan, ledger, handoff unless another session must resume
Proof and stop: deterministic compatibility proof passes, then stop
```

### Task 7 style scope pressure

The lesson from Task 7 was not "always use more process." It was that stronger
routes helped when they bought back attention on compatibility seams, test
integrity, and invalidation.

Under scope pressure:

- do not add artifacts just to feel safer
- do escalate when public behavior, compatibility seams, or test meaning may drift
- reserve proof for the risky seam, not just the happy path
- stop the loop when the route is no longer protecting the real failure mode

That often means a Level 2 route with sharper proof, or a Level 3 gate when the
change is decision-impacting or hard to resume safely.

## Observed tradeoff

One controlled Task 7 Codex pair tested an additive ceremony protocol: a required
budget ledger and ceremony steps were appended to an already prescriptive
benchmark wrapper. The treatment reached first functional and bench-ready green
later than the control, but had a shorter post-bench-ready tail; total provider
activity was nearly tied. This motivated replacement routing plus a stronger stop
rule.

The result is suggestive only. It does not establish universal benefit or
universal failure, and it does not isolate the base skill from the
benchmark-specific wrapper and protocol. The revised design is a
benchmark-informed hypothesis awaiting another controlled pair.
