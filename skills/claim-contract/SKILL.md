---
name: claim-contract
description: Preserve important unsettled claims as falsifiable evidence contracts that future agents can adjudicate without reconstructing the original conversation.
---

# Claim Contract

## Purpose

Preserve important unsettled assertions in `CLAIMS.md` so a future agent can judge them
from evidence instead of inheriting confidence, folklore, or marketing language.

**A claim must be able to lose.**

Open claims are contracts for future evidence, not placeholders for confidence.

## When to use

Use when a claim:

- matters beyond the current task or session
- is specific enough to support or refute within a named scope
- has a plausible evidence path an agent can inspect
- would change documentation, design, positioning, or a workflow choice if judged

Do not create a claim entry merely because something is unknown, interesting, or possible.

`VERIFY.md` owns whether the current task satisfied its contract. `CLAIMS.md` owns broader
assertions that may require evidence across tasks, runs, models, or sessions.

## Inputs

- Existing `CLAIMS.md` when present
- The proposed claim and its intended scope
- High-fidelity evidence references such as benchmark outputs, tests, logs, reports, code,
  eval artifacts, or external sources
- A predeclared evaluation or adjudication rule when one exists
- Known counterevidence, caveats, and evidence gaps
- The decision that would change if the claim were supported or refuted

## Workflow

1. Rewrite the assertion as one bounded, falsifiable sentence.
2. Reject or narrow universal language that cannot be reasonably adjudicated.
3. Assign a stable claim ID such as `C001`. Do not recycle IDs.
4. Record the scope: task set, model/settings, population, time window, environment, or other
   boundary needed to keep the claim honest.
5. Record the decision impact: what would actually change if the claim is supported or
   refuted.
6. **Freeze the judge contract before collecting new evidence:**
   - `Support if:` the evidence condition that is sufficient for `SUPPORTED`
   - `Refute if:` the evidence condition that is sufficient for `REFUTED`
   - `Otherwise:` use `INCONCLUSIVE`
7. Prefer references to high-fidelity evidence over copying evidence into the ledger.
8. Record current evidence and counterevidence separately from the claim statement.
9. Name the smallest useful next adjudication step when the claim is still open.
10. When asked to judge a claim, read the referenced evidence and apply the frozen rule:
    - `SUPPORTED` — the scoped support condition is met
    - `REFUTED` — the scoped refutation condition is met
    - `INCONCLUSIVE` — evidence was evaluated but neither condition is met cleanly
    - `OPEN` — the claim remains judgeable but the required evidence has not been evaluated
    - `RETIRED` — the claim is no longer decision-relevant; this is not a truth judgment
11. Record exact evidence references and the commit, run, date, or version needed to identify
    what was judged.
12. If the claim or judge rule changes materially after evidence is observed,
    **do not move the goalposts.** Create a new claim ID and link the parent or superseded claim.
13. Keep resolved claims in the ledger or an explicit archive so future agents can see what
    was tested and why the status changed.

## Outputs

- `CLAIMS.md` entry with a stable claim ID
- `OPEN | SUPPORTED | REFUTED | INCONCLUSIVE | RETIRED` status
- Scoped claim statement
- Frozen support / refute / inconclusive rule
- High-fidelity evidence references and known gaps
- Next cheapest adjudication step for open claims
- Judgment provenance when a status changes

## Stop conditions

- The claim is scoped enough that an agent can identify evidence that would support or refute
  it.
- The judge contract is frozen before new evidence is used to change status.
- Current evidence and evidence gaps are distinguishable.
- A future agent can judge the claim without reconstructing the original chat.
- If no plausible falsifier or adjudication path exists, do not add the claim to the ledger.

## Anti-patterns

- Turning `CLAIMS.md` into a TODO list, roadmap, research diary, or marketing backlog.
- Creating entries for every uncertainty or implementation question.
- Using `SUPPORTED` to mean universally true outside the recorded scope.
- Treating one favorable example as sufficient when the judge contract requires broader
  evidence.
- Rewriting the support threshold after seeing the result.
- Hiding counterevidence or failed evaluations.
- Copying large evidence blobs into the ledger instead of referencing authoritative artifacts.
- Replacing `VERIFY.md` with a project-level claim ledger.
- Recording claims so broad that no practical evidence could refute them.
