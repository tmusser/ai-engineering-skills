---
name: grill-with-docs-lite
description: Groom a fuzzy request and the smallest relevant source set into a bounded PRE-SPEC ASSEMBLY packet for mini-spec, using optional read-only research fan-out while separating evidence, tensions, decisions, assumptions, and blockers before contract language is written.
---

# Grill With Docs Lite

## Purpose

Prepare trustworthy inputs for `mini-spec` before `SPEC.md` exists.

Turn a fuzzy but bounded AI-engineering request plus relevant docs/repo evidence into a compact **PRE-SPEC ASSEMBLY** packet. The packet should expose the source-backed facts, authority boundaries, contradictions, decision tensions, safe assumptions, verification anchors, and likely failure mode that `mini-spec` needs to assemble an auditable contract.

This is a pre-spec evidence-grooming gate, not a requirements author and not a domain-modeling workflow. It may use bounded research fan-out to inspect independent evidence seams, but the parent agent owns synthesis and judgment. It must not silently promote guesses, scout conclusions, implementation details, or source silence into contract language.

`PRE-SPEC ASSEMBLY` replaces the older `CLARIFICATION DELTA` shape while preserving the same bounded pre-spec role.

## When to use

Use when the task is probably small enough for `mini-spec`, but the request is still conversationally fuzzy or relevant docs/code may change the objective, acceptance boundary, compatibility surface, tradeoff, or proof target.

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

Source silence is not a `FACT`. An implementation detail is not automatically a requirement. A research scout's summary is not evidence unless its cited source supports the claim.

## Research fan-out

Keep research bounded and read-only. The goal is faster evidence gathering, not a committee of agents inventing requirements.

Use delegated or parallel research when at least two independent evidence seams can be investigated without depending on each other's results. Typical seams include public contract/tests, compatibility callers, migration history, permissions/security boundaries, and an external standard explicitly in scope.

If the runtime supports delegated agents:

- Launch at most 3 read-only research scouts after the parent has identified the likely authority surfaces.
- Give each scout one narrow question, one source boundary, and one stop condition.
- Ask each scout to return at most 5 decision-relevant findings, each with a source locator and `FACT` or `UNKNOWN` classification.
- Ask scouts to flag contradictions or tensions they can support with evidence, but not to resolve them.
- Scouts must not write files, draft requirements, make product decisions, or recursively delegate.
- The parent agent must reconcile overlaps and spot-check any scout claim that could change public behavior, schemas, security, permissions, compatibility, data semantics, or the verification target.

If delegated agents are unavailable, perform the same seam-by-seam research sequentially. Do not expand the source set merely to simulate fan-out.

External research is optional, not automatic. Use it only when the request asks for it or an in-scope authority boundary requires it. Prefer primary sources and mark freshness-sensitive evidence explicitly.

## Tradeoff and tension handling

Distinguish a contradiction from a tension:

- `CONTRADICTION` — two claims or constraints cannot both govern the slice as currently stated.
- `TENSION` — both sides may be valid, but favoring one creates a meaningful cost for the other.

Only surface tensions grounded in the request or evidence. Do not manufacture generic pros/cons.

For each material tension, record:

`TENSION — <pole A> ↔ <pole B> — evidence: <locators> — favor A: <consequence> — favor B: <consequence> — status: RESOLVED | DECISION_REQUIRED`

Prioritize tensions that affect public behavior, compatibility, security, permissions, data semantics, irreversibility, scope, or the verification target. Low-consequence implementation preferences do not deserve a decision ceremony.

## Workflow

1. Read the smallest authority-bearing source set before asking questions.
2. Identify what each source actually governs. Prefer the richest source of truth rather than paraphrasing it wholesale.
3. Identify independent evidence seams. When fan-out is justified, launch bounded research scouts while the parent continues reading the primary authority source.
4. Reconcile scout findings against the cited sources. Deduplicate overlaps, reject unsupported summaries, and keep unresolved evidence as `UNKNOWN`.
5. Extract only evidence that can change the spec's objective, acceptance boundary, non-goals, compatibility seams, invalid-if conditions, material tradeoffs, or verification demo.
6. Classify unresolved points as `FACT`, `DECISION`, `ASSUMPTION`, or `UNKNOWN`.
7. Build an **authority map**: reference -> governed behavior/decision -> task-specific delta (`none`, explicit delta, or `unresolved`).
8. Hunt for contradictions between the request, source facts, existing behavior, non-goals, constraints, and other authoritative sources.
9. Build a **tension map** for evidence-backed tradeoffs that could change the contract even when no literal contradiction exists.
10. Answer from docs or code when the repository can settle the point; do not ask the user to repeat discoverable facts.
11. Prioritize unresolved decisions by consequence: contradictions first, then high-impact tensions, then lower-risk ambiguity. Prefer one question that resolves several downstream uncertainties.
12. Ask only questions whose answers can materially change the eventual spec. Default question budget: at most 3.
13. When asking, use the anatomy **evidence -> contradiction, tension, or absence -> options -> consequence -> decision**. Make the cost of each meaningful option visible rather than asking a generic discovery question.
14. Carry an `ASSUMPTION` only when it is reversible and low-risk. If it changes public behavior, schema, permissions, security, data semantics, compatibility, or the verification target, treat it as a `DECISION` or `UNKNOWN` instead.
15. Groom the resolved material into spec ingredients: objective candidate, acceptance signals, boundaries, compatibility constraints, verification anchors, primary failure-mode candidate, invalid-if candidates, and resolved tradeoff posture.
16. Do not update `CONTEXT.md`, create glossary entries, or write ADRs as part of this skill. Do not draft `SPEC.md` here.
17. Emit one compact **PRE-SPEC ASSEMBLY** packet and stop.
18. If important ambiguity cannot fit the bounded question budget without hiding consequential decisions, route to a fuller clarification/domain-model workflow instead of expanding this skill.

## Question shape

Bad:

> What should the export format be?

Better:

> `tests/export_contract.py` treats `total` as the public header, while the request implies renaming it to `amount`. That creates a compatibility ↔ cleanup tension: preserving `total` avoids breaking consumers, adding both names preserves compatibility but carries temporary duplication, and replacing it outright gives the cleanest contract but requires a migration. Which posture should this slice take?

The question should expose why the answer matters to the eventual contract and what is paid for each meaningful choice.

## Outputs

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
- CONTRADICTION — request ↔ source — ...
- CONTRADICTION — source ↔ source — ...

Tension map:
- TENSION — ... ↔ ... — evidence: ... — favor A: ... — favor B: ... — status: RESOLVED | DECISION_REQUIRED

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
- `BLOCKED` — an unresolved decision/unknown can change objective, acceptance, authority, compatibility, invalid-if boundaries, material tradeoff posture, or verification.

Do not use `READY_WITH_ASSUMPTIONS` to smuggle a consequential product or technical choice past the user.

## Handoff to mini-spec

`mini-spec` may promote resolved user intent and source-backed evidence into contract language.

It must not silently promote:

- an `ASSUMPTION` into a requirement;
- source silence into a non-goal;
- an implementation detail into an acceptance criterion;
- a scout summary into a fact without source support;
- an unresolved conflict or tension into a task-specific delta;
- an `UNKNOWN` into a working fact.

The expected mapping is:

- objective candidate -> Objective
- authority map -> Authoritative references + task-specific delta
- acceptance signals -> Acceptance criteria
- non-goals / boundaries -> Non-goals + spec ceiling
- constraints / compatibility seams -> Compatibility seams / invalid-if constraints
- tension map -> explicit tradeoff posture where contract-relevant
- verification anchors -> Verification demo
- primary failure-mode candidate -> Likely failure modes / primary failure mode
- decisions / unknowns -> Open questions until resolved

## Success looks like

- `mini-spec` receives clean ingredients instead of conversational mush.
- Independent evidence seams were researched in parallel when that reduced latency without widening scope.
- Source-backed facts remain distinguishable from user choices, scout summaries, and assumptions.
- Contradictions and material tensions are visible before they can be laundered into `SPEC.md` as equally authoritative prose.
- The agent asked no question that available docs or code could answer.
- The user sees the real cost of meaningful choices instead of a generic list of pros and cons.
- The packet is compact enough to feed directly into `mini-spec` without becoming a parallel requirements document.

## Stop conditions

- `Mini-spec readiness: READY`.
- `Mini-spec readiness: READY_WITH_ASSUMPTIONS`, with only reversible low-risk assumptions.
- `Mini-spec readiness: BLOCKED` because a consequential decision or unknown remains.
- The default question budget is exhausted and important ambiguity remains -> route to a fuller workflow.

## Anti-patterns

- Launching research scouts before identifying a bounded evidence seam.
- Letting scouts make product decisions, write files, or recursively delegate.
- Treating a scout summary as authoritative without checking its cited source.
- Manufacturing generic tradeoffs that are not grounded in the request or evidence.
- Listing pros and cons without stating the consequence of favoring either side.
- Drafting `SPEC.md` inside the grill step.
- Turning an implementation observation into a requirement without user/source authority.
- Treating source silence as a non-goal or source-backed fact.
- Asking generic discovery questions without showing the evidence and consequence.
- Building a glossary or ADR trail during a lite pre-spec pass.
- Walking every branch of a decision tree after the bounded slice is already clear.
- Asking the user for information the repository can answer.
- Starting implementation before pre-spec readiness is established.
