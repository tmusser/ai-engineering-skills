---
name: grill-with-docs-lite
description: Groom a fuzzy request and the smallest relevant source set into a bounded PRE-SPEC ASSEMBLY packet for mini-spec, separating evidence from decisions, assumptions, and blockers before contract language is written.
---

# Grill With Docs Lite

## Purpose

Prepare trustworthy inputs for `mini-spec` before `SPEC.md` exists.

Turn a fuzzy but bounded AI-engineering request plus relevant docs/repo evidence into a compact **PRE-SPEC ASSEMBLY** packet. The packet should expose the source-backed facts, authority boundaries, contradictions, decisions, safe assumptions, verification anchors, and likely failure mode that `mini-spec` needs to assemble an auditable contract.

This is a pre-spec evidence-grooming gate, not a requirements author and not a domain-modeling workflow. It must not silently promote guesses, implementation details, or source silence into contract language.

## When to use

Use when the task is probably small enough for `mini-spec`, but the request is still conversationally fuzzy or relevant docs/code may change the objective, acceptance boundary, compatibility surface, or proof target.

Skip it when the request is already crisp enough to write a bounded spec directly.

Use a fuller domain-model or architecture workflow instead when the work requires canonical vocabulary, multiple hard-to-reverse architectural decisions, cross-context modeling, or an open-ended decision tree.

## Inputs

- User request
- Existing notes or docs
- Relevant repo files
- `CONTEXT.md` if present

## Evidence classes

Every unresolved or decision-relevant item must stay visibly classified until `mini-spec` assembles the contract:

- `FACT` — supported by a source; include the file/path, symbol, test, artifact, URL, or other locator.
- `DECISION` — requires an explicit user/product choice before it can become contract language.
- `ASSUMPTION` — a reversible working default that does not silently alter public behavior, schemas, security, permissions, data semantics, or compatibility.
- `UNKNOWN` — missing evidence that blocks safe specification or must remain explicitly unresolved.

Source silence is not a `FACT`. An implementation detail is not automatically a requirement.

## Workflow

1. Read the smallest relevant source set before asking questions.
2. Identify what each source actually governs. Prefer the richest source of truth rather than paraphrasing it wholesale.
3. Extract only evidence that can change the spec's objective, acceptance boundary, non-goals, compatibility seams, invalid-if conditions, or verification demo.
4. Classify unresolved points as `FACT`, `DECISION`, `ASSUMPTION`, or `UNKNOWN`.
5. Build an **authority map**: reference -> governed behavior/decision -> task-specific delta (`none`, explicit delta, or `unresolved`).
6. Hunt for contradictions between the request, source facts, existing behavior, non-goals, constraints, and other authoritative sources.
7. Answer from docs or code when the repository can settle the point; do not ask the user to repeat discoverable facts.
8. Ask only questions whose answers can materially change the eventual spec. Default question budget: at most 3.
9. When asking, use the anatomy **evidence -> contradiction or absence -> decision -> consequence**. Make the tradeoff visible rather than asking a generic discovery question.
10. Carry an `ASSUMPTION` only when it is reversible and low-risk. If it changes public behavior, schema, permissions, security, data semantics, compatibility, or the verification target, treat it as a `DECISION` or `UNKNOWN` instead.
11. Groom the resolved material into spec ingredients: objective candidate, acceptance signals, boundaries, compatibility constraints, verification anchors, primary failure-mode candidate, and invalid-if candidates.
12. Do not update `CONTEXT.md`, create glossary entries, write ADRs, or draft `SPEC.md` as part of this skill.
13. Emit one compact **PRE-SPEC ASSEMBLY** packet and stop.
14. If important ambiguity cannot fit the bounded question budget without hiding consequential decisions, route to a fuller clarification/domain-model workflow instead of expanding this skill.

## Question shape

Bad:

> What should the export format be?

Better:

> `tests/export_contract.py` treats `total` as the public header, while the request implies renaming it to `amount`. Should this slice intentionally change that output contract or preserve `total`? Changing it may break existing consumers.

The question should expose why the answer matters to the eventual contract.

## Output

Use this compact shape:

```text
PRE-SPEC ASSEMBLY

Request intent:
- ...

Authority map:
- [reference] — governs: ... — task-specific delta: none | ... | unresolved

Source-backed facts:
- FACT — ... [locator]

Spec ingredients:

Objective candidate:
- ...

Acceptance signals:
- REQUEST — ...
- SOURCE — ... [locator]

Non-goals / boundaries:
- ...

Constraints / compatibility seams:
- ...

Verification anchors:
- ...

Primary failure mode candidate:
- ...

Invalid-if candidates:
- ...

Contradictions:
- request ↔ source — ...
- source ↔ source — ...

Decisions required:
- DECISION — ...

Assumptions carried:
- ASSUMPTION — ...

Open unknowns:
- UNKNOWN — ...

Mini-spec readiness:
READY | READY_WITH_ASSUMPTIONS | BLOCKED
```

The packet is input to `mini-spec`; it is not a replacement for `SPEC.md` and should not survive as a second durable source of truth unless another workflow explicitly chooses to persist it.

## Readiness gate

Use:

- `READY` — evidence and decisions are sufficient for `mini-spec`; no consequential ambiguity remains.
- `READY_WITH_ASSUMPTIONS` — only safe, reversible assumptions remain and each is explicitly labeled.
- `BLOCKED` — an unresolved decision/unknown can change objective, acceptance, authority, compatibility, invalid-if boundaries, or verification.

Do not use `READY_WITH_ASSUMPTIONS` to smuggle a consequential product or technical choice past the user.

## Handoff to mini-spec

`mini-spec` may promote resolved user intent and source-backed evidence into contract language.

It must not silently promote:

- an `ASSUMPTION` into a requirement;
- source silence into a non-goal;
- an implementation detail into an acceptance criterion;
- an unresolved conflict into a task-specific delta;
- an `UNKNOWN` into a working fact.

The expected mapping is:

- objective candidate -> Objective
- authority map -> Authoritative references + task-specific delta
- acceptance signals -> Acceptance criteria
- non-goals / boundaries -> Non-goals + spec ceiling
- constraints / compatibility seams -> Compatibility seams / invalid-if constraints
- verification anchors -> Verification demo
- primary failure-mode candidate -> Likely failure modes / primary failure mode
- decisions / unknowns -> Open questions until resolved

## Success looks like

- `mini-spec` receives clean ingredients instead of conversational mush.
- Source-backed facts remain distinguishable from user choices and assumptions.
- Contradictions are visible before they can be laundered into `SPEC.md` as equally authoritative prose.
- The agent asked no question that available docs or code could answer.
- The packet is compact enough to feed directly into `mini-spec` without becoming a parallel requirements document.

## Stop conditions

- `Mini-spec readiness: READY`.
- `Mini-spec readiness: READY_WITH_ASSUMPTIONS`, with only reversible low-risk assumptions.
- `Mini-spec readiness: BLOCKED` because a consequential decision or unknown remains.
- The default question budget is exhausted and important ambiguity remains -> route to a fuller workflow.

## Anti-patterns

- Drafting `SPEC.md` inside the grill step.
- Turning an implementation observation into a requirement without user/source authority.
- Treating source silence as a non-goal or source-backed fact.
- Asking generic discovery questions without showing the evidence and consequence.
- Building a glossary or ADR trail during a lite pre-spec pass.
- Walking every branch of a decision tree after the bounded slice is already clear.
- Asking the user for information the repository can answer.
- Starting implementation before pre-spec readiness is established.
