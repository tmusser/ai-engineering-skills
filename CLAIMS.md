# Claims

> Open, bounded claims that remain worth adjudicating. These are not current marketing claims.
> A claim may be plausible and still remain `OPEN` until its frozen judge contract is met.

## Status semantics

- `OPEN` — judgeable claim; required evidence has not yet been evaluated sufficiently.
- `SUPPORTED` — the recorded support condition is met within the stated scope.
- `REFUTED` — the recorded refutation condition is met within the stated scope.
- `INCONCLUSIVE` — evidence was evaluated but neither condition resolves the claim cleanly.
- `RETIRED` — no longer decision-relevant; this is not a truth judgment.

## Active claims

### C001 — Fresh-session evidence advantage

- Status: OPEN
- Claim: On resume-sensitive `agent-workflow-bench` tasks, a skill-routed workflow leaves
  more complete fresh-session audit/resume evidence than a matched strong-prompt control
  without reducing hidden functional correctness.
- Scope: Matched runs on benchmark tasks with resume or artifact evaluators, holding task
  version, model, model settings, and evaluator version fixed within each comparison.
- Decision impact: Determines whether the repo can make a comparative resumability claim
  rather than the current narrower claim that it produces auditable, resumable artifacts.
- Support if: A predeclared repeated-run protocol shows a higher aggregate resume/artifact
  evidence score for the skill-routed arm and no lower hidden functional pass rate.
- Refute if: The same protocol shows no aggregate resume/artifact advantage or a lower hidden
  functional pass rate for the skill-routed arm.
- Otherwise: INCONCLUSIVE
- Evidence references: `docs/benchmark-findings.md` and
  <https://github.com/tmusser/agent-workflow-bench>.
- Current evidence: Pilot results are suggestive for auditability/resume artifacts, but the
  repository does not currently claim broad comparative superiority.
- Counterevidence / gaps: Limited tasks, models, seeds, and repeated matched runs.
- Next cheapest adjudication: Predeclare an aggregate rule, then repeat paired runs on the
  existing resume-sensitive benchmark tasks across multiple seeds.
- Last judged: never
- Parent / supersedes: none

### C002 — Ceremony routing reduces process tail

- Status: OPEN
- Claim: On low-risk tasks where a lighter route is sufficient, `ceremony-budget` reduces
  post-ready process overhead relative to an additive full-governance route without weakening
  required proof.
- Scope: Matched task/model/settings runs where both routes have the same acceptance criteria,
  compatibility seams, and proof obligations.
- Decision impact: Determines whether ceremony routing can be positioned as an efficiency
  improvement rather than only a qualitative workflow option.
- Support if: The lighter route has lower median post-ready turns while required proof-validity
  and hidden functional outcomes are no worse than the additive route.
- Refute if: Post-ready turns do not decrease, or proof-validity / hidden functional outcomes
  are worse under the lighter route.
- Otherwise: INCONCLUSIVE
- Evidence references: `docs/benchmark-findings.md` and Task 7 evidence in
  <https://github.com/tmusser/agent-workflow-bench>.
- Current evidence: Task 7 motivated replacement routing and proof reserve, but does not prove
  a general efficiency advantage.
- Counterevidence / gaps: No repeated cross-task comparison focused on post-ready process tail.
- Next cheapest adjudication: Add a matched repeated protocol that records first-functional-
  green turn, final-proof turn, proof validity, and hidden outcome.
- Last judged: never
- Parent / supersedes: none

### C003 — Reference-first specs reduce lossy duplication

- Status: OPEN
- Claim: On tasks with high-fidelity authoritative references, reference-first specs reduce
  duplicated specification text without increasing contract violations relative to equivalent
  prose-restated specs.
- Scope: Matched tasks with usable tests, code, schemas, mockups, rubrics, or source
  implementations that can serve as authoritative references.
- Decision impact: Determines whether reference-first specification should be positioned as an
  empirically supported context-efficiency improvement rather than only a design principle.
- Support if: The reference-first arm has lower duplicated-spec text while hidden-contract or
  acceptance-criterion failure rate is no higher than the prose-restated arm.
- Refute if: Duplicated-spec text does not decrease, or contract failures increase in the
  reference-first arm.
- Otherwise: INCONCLUSIVE
- Evidence references: `skills/mini-spec/SKILL.md`, `templates/SPEC.md`, and future benchmark
  artifacts that exercise rich references.
- Current evidence: The rule is newly adopted; no controlled comparison currently supports the
  empirical claim.
- Counterevidence / gaps: No paired evaluation yet and no frozen duplication metric.
- Next cheapest adjudication: Define a deterministic duplication metric and run paired tasks
  whose behavior is already expressed by tests or code references.
- Last judged: never
- Parent / supersedes: none

## Resolved / retired claims

_None yet._
