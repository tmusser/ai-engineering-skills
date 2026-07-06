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

Usually a short decision block, not a durable file:

```text
CEREMONY BUDGET
Level: 0 | 1 | 2 | 3
Use: ...
Skip: ...
Proof reserve: ...
Stop rule: ...
```

Do not create `CEREMONY_BUDGET.md` by default. A durable routing note is optional
and only justified for higher-risk work where the routing decision itself needs to
survive a handoff or audit.

## Levels

### Level 0

Tiny reversible patch.

- Use: direct patch plus one sanity check
- Typical skips: `mini-spec`, `thin-plan`, `handoff`
- Proof reserve: one command, smoke path, or direct behavior check

### Level 1

One bounded slice with low ambiguity but enough behavior change to justify an
explicit boundary and proof.

- Use: `scope-freeze -> build-one -> verify-contract`
- Typical skips: `mini-spec` unless ambiguity appears, `thin-plan`, `handoff`
- Proof reserve: a bounded verification record tied to the changed behavior

### Level 2

Small vertical slice with real ambiguity, moderate scope pressure, or a genuine
risk that weak proof will be mistaken for done.

- Use: `mini-spec -> optional thin-plan -> scope-freeze -> build-one -> test-mini -> verify-contract`
- Typical skips: `checklist-mini`, `analyze-mini`, `ship-mini` unless risk rises
- Proof reserve: explicit acceptance criteria and deterministic verification

### Level 3

User-facing, scheduled, autonomous, decision-impacting, data-sensitive, risky, or
multi-slice work.

- Use: `grill-with-docs-lite -> mini-spec -> checklist-mini -> thin-plan -> scope-freeze -> analyze-mini -> build-one -> test-mini -> verify-contract -> ship-mini -> handoff`
- Typical skips: only skills that clearly do not apply
- Proof reserve: durable verification, explicit guardrails, and safe resume state

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

### Tiny README typo

```text
Level: 0
Use: direct patch -> markdownlint
Skip: mini-spec, verify-contract artifact, handoff
Proof reserve: clean lint result
Stop rule: stop after the one-file check passes
```

### Small bounded bug fix

```text
Level: 1
Use: inline scope-freeze -> build-one -> verify-contract
Skip: mini-spec unless reproduction or acceptance criteria are still fuzzy
Proof reserve: one targeted test or smoke path
Stop rule: stop after the behavior change is verified
```

### Small feature with real ambiguity

```text
Level: 2
Use: mini-spec -> optional thin-plan -> scope-freeze -> build-one -> test-mini -> verify-contract
Skip: ship-mini, handoff unless the slice becomes shared or resumed later
Proof reserve: explicit acceptance criteria plus deterministic verification
Stop rule: stop after one verified slice, not after "mostly working"
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
