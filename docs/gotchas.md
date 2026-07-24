# Optional Gotchas Artifact

`GOTCHAS.md` is an optional durable record for non-obvious project sharp edges that are
likely to surprise another session or agent.

It is deliberately narrower than a bug log and more durable than the traps section in a
single handoff.

## Promotion rule

Create or update `GOTCHAS.md` only when all of these are true:

- the behavior or constraint is non-obvious
- ignoring it has a meaningful consequence
- another session, agent, or nearby task is likely to encounter it again
- the entry can point to evidence such as code, a command, a test, an issue, or a commit

Do not create the artifact merely because a task was difficult.

## Artifact boundaries

- `BUGS.md` records an active defect, reproduction, hypothesis, and resolution work.
- `HANDOFF.md` records the current continuation state and session-specific traps.
- `DECISIONS.md` records choices and rationale.
- `GOTCHAS.md` records recurring sharp edges and the safe path around them.

A one-off trap can stay in `HANDOFF.md`. Promote it to `GOTCHAS.md` when it becomes a
reusable defensive constraint. When a gotcha matters to the next task, the handoff should
reference the gotcha ID instead of copying the full entry.

## Entry shape

Keep each entry compact and grounded:

```text
G1 - Generated client must follow schema regeneration
Trigger: editing generated API client code
Gotcha: direct edits are overwritten by the generator
Consequence: the apparent fix disappears on regeneration
Safe path: change the schema/template and regenerate
Evidence: scripts/generate_client.py; python tests/test_generated_client.py
Last verified: 2026-07-24
Status: active
```

The important fields are the trigger, consequence, safe path, and evidence. `Last
verified` makes aging visible; it is not a TTL or proof that the gotcha is still true.
Resolved or contradicted entries should be removed or marked resolved instead of living
forever as project folklore.

## Packet routing

The repository route map includes an optional `Gotchas / sharp edges` route. Requests
containing terms such as `gotcha`, `trap`, `sharp edge`, `footgun`, `quirk`, `caveat`, or
`pitfall` can select a live `GOTCHAS.md` ahead of the reusable template.

When a task is already known to cross a recorded sharp edge, make the dependency
explicit rather than hoping keyword routing catches it:

```bash
python scripts/context_pack.py \
  "resume the export change without crossing known sharp edges" \
  --require-file GOTCHAS.md \
  --strict
```

That makes the packet record `GOTCHAS.md` as a required represented source, including
its selected range and content hash.

## Handoff integration

`HANDOFF.md` remains the launchpad. If an active gotcha affects the next task:

1. reference its ID in the resume packet or traps section
2. include `GOTCHAS.md` in the read-first set
3. use `--require-file GOTCHAS.md` when generating a packet for that continuation
4. do not duplicate the full gotcha into the handoff

This keeps the handoff dense while making recurring project hazards harder to lose.

## Failure boundaries

- `GOTCHAS.md` is optional; absence is not a workflow failure.
- Do not promote ordinary TODOs, generic best practices, or transient debugging guesses.
- Do not treat an old gotcha as authoritative when live code or verification contradicts it.
- Do not let the artifact replace tests, verification, or direct inspection of the affected code.
- Do not record secrets, credentials, private URLs, or sensitive operational data.
