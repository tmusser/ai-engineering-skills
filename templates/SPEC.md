# Spec

## Objective

_Describe the smallest useful objective._

## User / use case

_Describe who needs this and why._

## Acceptance criteria

- _TBD_

## Non-goals

- _TBD_

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
- weakens or rewrites existing tests merely to fit the implementation
- changes fixture/source data without explicit approval
- preserves behavior only through a new alternate path while breaking the old path
- changes forbidden/protected files
- adds dependencies or framework changes outside scope
