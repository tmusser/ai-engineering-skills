# Why Skills, Not Prompts

A prompt asks for behavior once.
A skill makes the expected behavior explicit, inspectable, recoverable, and
gateable across sessions.
Templates preserve state.
Verification artifacts make claims auditable.

That difference matters when you are working with coding agents. A one-off prompt can
be useful for a single reply, but it does not give the next session a stable
operating shape.

## What prompts can do

A prompt can get an agent started quickly. It can shape tone, suggest a checklist, or
ask for a specific output. That is useful, but it is also fragile.

A prompt depends on the current conversation. Once the session changes, the prompt
may no longer be visible, remembered, or followed the same way.

## What a skill can do

A skill gives the same behavior a stable home.

It tells the agent when to use the procedure, what inputs it needs, how to work, what
to output, and when to stop. Because the skill is stored as a file, it can be reused
across sessions and projects. It can also be paired with templates and verification
notes so the next session does not need to reconstruct the whole situation from chat.

## Failure modes this catches

- Scope creep
- Fake verification
- Unrelated file edits
- Lost handoff context
- Debugging without reproduction

These are not rare edge cases. They are the usual ways agent work goes off track when
the workflow is only a prompt.

## The uncomfortable possibility

For many tasks, a strong model with a clear prompt and good tests may match or beat a
heavier skill workflow. More process can add tokens, contradictions, maintenance, and
false confidence.

The point of this repo is not to make the agent smarter. The point is to make the
work easier to inspect, resume, and verify.

## Value hierarchy

1. Deterministic checks
2. Tests, evals, and protected-path gates
3. Durable artifacts
4. Named lightweight rituals
5. Long behavioral instruction packs

More process is not better. More durable signal is better.

## Plan Mode and the practical rule

Plan Mode is useful. This repo adds an earlier question before plan approval:
is this the right bounded work? It also adds later checks for evidence and restart
state.

Use prompts for one-off direction.
Use skills when you want the expected behavior to be explicit, inspectable,
recoverable, and gateable across sessions.
Use templates when the next session needs durable context.
Use verification when the work should be auditable.
Use loops only when they are bounded by an objective signal, a budget, a rollback
rule, a ledger, and a stop condition. Otherwise they are just automated drift. See
[Loop governance](loop-governance.md).

## Process theater caveat

This can become theater if you use too much of it. The repo is designed around small
gates that catch misalignment early, not ceremony for its own sake.
