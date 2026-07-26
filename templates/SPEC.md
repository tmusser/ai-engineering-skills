# Spec

## Contract identity (optional)

Contract ID: _TBD_ | Parent: _none_ | Base commit: _TBD_ | Issued: _TBD_
Replan reason: _none_

## Objective

_Describe the smallest useful objective._

## User / use case

_Describe who needs this and why._

## Acceptance criteria

- _TBD_

## Non-goals

- _TBD_

## Spec ceiling

Acceptance criteria are the required floor. Do not add user-visible behavior, APIs,
schema changes, refactors, dependencies, or adjacent cleanup beyond what is necessary
to satisfy them. If correctness requires expansion, update or renegotiate the spec before
implementing that expansion.

## Loop contract

_When repeated iterations are expected, define the loop before running it._

- Artifact being improved: _TBD_
- Feedback signal: _TBD_
- Acceptance threshold: _TBD_
- Budget / max iterations: _TBD_
- Revert rule: _TBD_
- Ledger location: _TBD_
- Stop condition: _TBD_
- Human review trigger: _TBD_

## Likely failure modes

Check the risks this spec is meant to prevent.

- [ ] Premature agreement on vague scope
- [ ] Hidden non-goals
- [ ] Over-broad file changes
- [ ] Unclear acceptance criteria
- [ ] Unverified success claim
- [ ] Context drift / forgotten constraint
- [ ] Hallucinated dependency or API behavior
- [ ] Refactor disguised as a small fix
- [ ] Multiple tasks bundled as one request
- [ ] Helpful extra behavior beyond the spec
- [ ] Other: _TBD_

Primary failure mode for this slice:

> _TBD_

If none apply, use a lighter workflow.

## Constraints

- _TBD_

## Commands

- Run: _TBD_
- Test: _TBD_
- Build: _TBD_
- Verify: _TBD_

## Project structure

- _TBD_

## Verification demo

- _TBD_

## Open questions

- _TBD_

## Compatibility seams to preserve

When applicable, list behavior that must remain import-compatible or output-compatible.

- Public imports / APIs: _TBD_
- CLI commands / flags: _TBD_
- JSON/schema/output contracts: _TBD_
- Existing tests whose meaning must remain valid: _TBD_
- Data/fixture semantics: _TBD_

## Invalid if

- breaks a named compatibility seam
- implements an explicit non-goal or adds adjacent behavior not required by an acceptance criterion
- weakens or rewrites existing tests merely to fit the implementation
- changes fixture/source data without explicit approval
- preserves behavior only through a new alternate path while breaking the old path
- changes forbidden/protected files
- adds dependencies or framework changes outside scope
