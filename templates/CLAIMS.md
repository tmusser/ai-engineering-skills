# Claims

> Durable ledger for bounded assertions that remain worth adjudicating. A claim must be able
> to lose. Reference evidence; do not turn this file into a results dump.

## Status semantics

- `OPEN` — judgeable claim; required evidence has not yet been evaluated.
- `SUPPORTED` — the recorded support condition is met within the stated scope.
- `REFUTED` — the recorded refutation condition is met within the stated scope.
- `INCONCLUSIVE` — evidence was evaluated but neither condition resolves the claim cleanly.
- `RETIRED` — no longer decision-relevant; this is not a truth judgment.

## Active claims

### C001 — _Short label_

- Status: OPEN
- Claim: _One bounded, falsifiable sentence._
- Scope: _Task/model/population/time/environment boundary._
- Decision impact: _What changes if supported or refuted._
- Support if: _Predeclared sufficient evidence condition._
- Refute if: _Predeclared sufficient counterevidence condition._
- Otherwise: INCONCLUSIVE
- Evidence references: _Paths, run IDs, reports, commits, URLs, or none yet._
- Current evidence: _What is already known without overstating it._
- Counterevidence / gaps: _Known conflicts, missing coverage, or uncertainty._
- Next cheapest adjudication: _Smallest useful test or evaluation._
- Last judged: _never | date + commit/run/version_
- Parent / supersedes: _none | claim ID_

## Resolved / retired claims

_Move claims here without erasing their judge contract or evidence provenance._
