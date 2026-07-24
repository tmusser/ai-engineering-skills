---
name: handoff
description: Compress project context into HANDOFF.md with workflow state, active modes, next gate, verification, current hypothesis, freshness anchors, optional gotcha references, and a resume packet for the next agent session.
---

# Handoff

## Purpose

Compress context into a launchpad for the next session. A handoff is not a transcript — it is durable state that lets a fresh agent continue safely without the full chat history.

A handoff is also not authoritative merely because the file exists. When Git state is available, establish freshness before trusting an existing `HANDOFF.md`.

## When to use

Use at the end of a session, before switching agents, or before pausing work.

When resuming from an existing handoff, apply the freshness check before using its status, next task, or verification claims as current state.

## Inputs

- SPEC.md, PLAN.md, TODO.md, VERIFY.md
- Optional `GOTCHAS.md` when recurring project sharp edges have been recorded
- Active modes, current phase, next gate
- Compatibility seams, invalid-if constraints, verify gate status, review-required items, next gate command when relevant
- Context risk level
- Active debugging hypothesis (if any)
- When relevant, carry loop state forward: iterations attempted, best known artifact,
  rejected attempts, current feedback signal, remaining budget, stop condition, and
  human review trigger.
- Branch, commit, dirty state
- Changed files, working/failing commands, unverified files
- Important decisions, open decisions, traps
- Freshness anchors when Git state is available: snapshot commit + workspace fingerprint

## Freshness rule

The bundled `scripts/handoff_freshness.py` helper lives inside this skill directory.
Resolve the active `handoff` skill directory, then use the helper to stamp and check
`HANDOFF.md`.

Status semantics:

- `PASS` — non-handoff repository state still matches the stamped snapshot.
- `STALE` — repository state changed after the handoff snapshot. Treat the handoff as advisory only, re-read live project state, and regenerate it before resuming.
- `REVIEW_REQUIRED` — freshness could not be established. Do not silently trust the handoff as current state.

The helper intentionally excludes `HANDOFF.md` itself from the workspace fingerprint so
editing or committing only the handoff does not invalidate its own snapshot.

If the helper cannot be executed, compare the recorded commit, dirty state, changed files,
and live Git status manually. Any mismatch or unresolved uncertainty is
`REVIEW_REQUIRED`, not an implicit pass.

## Gotcha promotion rule

Keep one-off continuation traps in `HANDOFF.md`. Promote a trap to optional `GOTCHAS.md`
only when it is non-obvious, has a meaningful consequence, is likely to recur across
sessions or nearby tasks, and can be grounded in evidence.

A promoted gotcha should record a stable ID, trigger, consequence, safe path, evidence,
last verification, and active/resolved status. When it affects the next task, reference
the gotcha ID from the handoff instead of copying the whole entry.

Do not turn `GOTCHAS.md` into a generic bug log, TODO list, or folklore file. `BUGS.md`
owns active defects; `GOTCHAS.md` owns recurring sharp edges.

## Workflow

1. Read current artifacts first.
2. If an existing `HANDOFF.md` will be used for resume, check freshness before trusting it.
3. Create or update HANDOFF.md starting with a **Resume Packet** block.
4. Record Workflow State (active modes, phase, loop, next gate, context risk, hypothesis).
5. Record continuation guardrails when relevant: compatibility seams preserved, invalid-if constraints, verify gate status, review-required items, next gate command.
6. State the current goal in 1-2 sentences.
7. List completed slices + verification results.
8. List changed files with one-line purpose (flag unverified).
9. Record working commands, known failing commands, important decisions, open decisions, and traps.
10. Promote recurring evidence-backed traps to `GOTCHAS.md`; keep one-off session traps in the handoff.
11. If an active gotcha affects the next task, reference its ID and make `GOTCHAS.md` part of the read-first set. When generating a context packet for that continuation, prefer `--require-file GOTCHAS.md` so the dependency is explicit.
12. Name **exactly one** next recommended task + its verification command.
13. After the final non-handoff project edit, stamp the freshness anchors with the bundled helper.
14. Run the helper's `check` command. Only `PASS` should be treated as a fresh handoff when the helper is available.
15. Keep under 120 lines unless complexity requires more.

**Resume Packet example (place near top):**

```text
RESUME PACKET

* Goal: ...
* Workflow State: lean-mode active, next gate=verify-contract, risk=low
* Branch: main, Commit: abc123, Dirty: no
* Freshness: PASS, Snapshot: abc123, Workspace: sha256:...
* Gotchas: G1, G3 | none
* Next task: ...
* Verification: `python test_mini.py --slice=foo`
* Read first: HANDOFF.md, GOTCHAS.md (if present/referenced), SPEC.md, PLAN.md, VERIFY.md (if present), then changed files below
```

## Outputs

- HANDOFF.md with Resume Packet + Workflow State
- Freshness anchors when Git state is available
- Optional references to active `GOTCHAS.md` entries that affect continuation
- Clear next task and verification path
- Continuation guardrails when relevant

## Success looks like

- A new agent can pick up the project from HANDOFF.md + core artifacts without rereading chat.
- All critical context (modes, risks, decisions, next gate) is in durable files.
- Exactly one next task is named.
- A stale handoff cannot silently outrank live repository state.
- A recurring sharp edge that matters to future work is not buried only in a one-session handoff.

## Stop conditions

- Next session can continue without full chat history.
- No important context lives only in memory.
- Next task and verification command are explicit.
- Freshness is `PASS` when the bundled helper is available; otherwise unresolved freshness is surfaced as `REVIEW_REQUIRED`.
- Relevant promoted gotchas are referenced without duplicating their full contents.

## Anti-patterns

- Writing a chat transcript summary instead of state.
- Vague status ("mostly done").
- Omitting active modes, failing commands, or dirty state.
- Carrying multiple debug hypotheses forward.
- No explicit next gate or verification.
- Treating `HANDOFF.md` as current merely because it exists.
- Continuing from a `STALE` or `REVIEW_REQUIRED` handoff without reconciling live state.
- Burying a recurring evidence-backed sharp edge only in `HANDOFF.md`.
- Creating `GOTCHAS.md` for ordinary bugs, temporary failures, or generic reminders.
