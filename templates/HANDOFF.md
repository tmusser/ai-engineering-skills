# Handoff

## Freshness

- Snapshot commit: `_TBD_`
- Workspace fingerprint: `_TBD_`
- Stamp after the final non-handoff edit: `python <handoff-skill-dir>/scripts/handoff_freshness.py stamp --handoff HANDOFF.md`
- Check before trusting this handoff: `python <handoff-skill-dir>/scripts/handoff_freshness.py check --handoff HANDOFF.md`

A `STALE` result means live repository state changed after this handoff was stamped. Re-read live project state and regenerate the handoff before resuming. `REVIEW_REQUIRED` means freshness could not be established and the handoff must not be treated as authoritative without inspection.

## Resume packet

Read first if present:

- `HANDOFF.md`
- `CONTEXT.md`
- `SPEC.md`
- `PLAN.md`
- `TODO.md`
- `VERIFY.md`

Resume command:

- _TBD_

## Workflow state

Active modes:

- lean-mode: on | off
- context-check: passive | explicit-only | off

Current phase:

- _TBD_

Current loop:

- _TBD_

Next gate:

- _TBD_

Context risk:

- _TBD_

Active hypothesis:

- _TBD_

## Continuation guardrails

- Compatibility seams preserved: _TBD_
- Invalid-if constraints: _TBD_
- Verify gate status: _TBD_
- Review-required items: _TBD_
- Next gate command: _TBD_

## Project goal

- _TBD_

## Current status

- _TBD_

## State IDs

Facts:

- F1: _TBD_

Decisions:

- D1: _TBD_

Assumptions:

- A1: _TBD_

Claims / numbers:

- C1: _TBD_

## Completed slices

- _TBD_

## Changed files

- _TBD_

## Commands that work

- _TBD_

## Known failing commands

- _TBD_

## Verification state

Last proof:

- _TBD_

Next verification command:

- _TBD_

## Loop state

_Use only when repeated iterations occurred or are expected._

- Iterations attempted:
- Best known artifact/state:
- Rejected attempts:
- Current feedback signal:
- Remaining budget:
- Stop condition:
- Next allowed iteration:
- Human review trigger:

## Open decisions

- _TBD_

## Traps / do-not-change notes

- _TBD_

## Next recommended task

- _TBD_
