# Limitations

<!-- markdownlint-disable MD013 -->

This repo reduces risk, but it does not replace judgment or make behavior deterministic.

## When not to use this repo

Do not reach for the full workflow when the task is obviously tiny:

- a typo, comment fix, or formatting cleanup
- a one-line configuration tweak
- a quick answer that does not change files
- a throwaway spike that will be discarded the same day

For those cases, use Level 0 or no workflow at all.

If the task grows beyond a reversible local change, start from the starter bundle in
[docs/bundles.md](docs/bundles.md) instead of jumping to the full path.

## When Level 0 is enough

Use Level 0 when the change is reversible, local, and easy to verify in one step. See
the [Ceremony ladder](README.md#ceremony-ladder) for how Level 0 fits with the larger
workflow.

Examples:

- renaming a variable
- adjusting a single doc sentence
- fixing a small shell flag
- changing one constant

If the work is still bounded but needs a little more shape, start from the starter
bundle in [docs/bundles.md](docs/bundles.md) instead of building a larger process.

## Where agents still fail

These skills improve behavior, but agents can still ignore a skill, partially follow a workflow, or:

- ignore a skill when the context gets long
- partially follow a workflow and skip the hard part
- restate the plan without tightening the scope
- make unrelated edits while trying to help
- miss a subtle constraint that was only implied in chat

That is why the repo keeps durable files and explicit checks instead of relying on
memory or assumptions.

## Where verification can still be insufficient

A passing command is not always enough.

Examples:

- a unit test passes but does not assert the user-visible output
- a smoke test covers the happy path but not the edge case
- command output looks right, but the underlying data is stale
- a script succeeds, but it never checked the exact contract you care about

Use [verify-contract](skills/verify-contract/SKILL.md) when you need durable evidence,
not just a green run.

## When scope-freeze blocks necessary exploration

`scope-freeze` is supposed to stop drift, not stop learning.

If exploration is truly needed:

1. pause the current slice
2. update the spec or scope explicitly
3. note the new boundary in `CONTEXT.md`, `SPEC.md`, or `HANDOFF.md`
4. resume with the new agreement

See [scope-freeze](skills/scope-freeze/SKILL.md) for the blast-radius boundary and
[handoff](skills/handoff/SKILL.md) for carrying the updated state forward.

## Autonomous and scheduled workflow cautions

Autonomous or scheduled agents need stricter gates than interactive sessions.

Use tighter scope, narrower commands, and clearer stop conditions when:

- a job runs without a human in the loop
- a schedule may repeat a flawed action
- the result has side effects outside the repo
- the agent can modify shared state or send messages

Before enabling a recurring or unattended workflow, prefer the smallest bundle that
still gives you verification and a rollback path.

If the work will ship or trigger downstream action, add
[ship-mini](skills/ship-mini/SKILL.md) and keep the evidence in
[verify-contract](skills/verify-contract/SKILL.md).

For delegated or scheduled tool-using workflows, see
[docs/agent-worker-safety.md](docs/agent-worker-safety.md).

## Recovery playbook

When the workflow gets in the way, do not push harder.

- pause feature work
- write down what changed in intent, scope, or evidence
- move the facts into `CONTEXT.md`, `SPEC.md`, or `HANDOFF.md`
- if needed, shrink to a smaller bundle from [docs/bundles.md](docs/bundles.md)
- if the current slice is blocked by uncertainty, add the missing assumption explicitly
  and continue from there

The escape hatch for `scope-freeze` is simple: pause, update the spec or scope
explicitly, then resume.

## What this repo does not promise

This repo does not promise that:

- an agent will follow instructions perfectly
- verification output proves the full real-world behavior
- a small workflow is always the right workflow
- autonomy is safe without tighter review and permissions
- one good run guarantees the next run will be good

It is meant to provide a practical way to make agent work easier to steer, easier to
verify, and easier to recover when things drift.
