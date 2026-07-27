---
name: workspace-checkpoint
description: Reactivate the smallest set of decision-governing constraints immediately before a consequential action, without introspection, full-context summarization, or a new durable artifact.
---

# Workspace Checkpoint

## Purpose

Re-center the next consequential action on the few current constraints and evidence that can change it.

**Reactivate, do not introspect.** This skill externalizes decision-relevant state; it does not ask the model to reveal private reasoning or claim access to internal representations.

**Checkpoint, do not summarize.** Read only the highest-authority sources needed for the next action and carry forward the smallest useful active set.

## When to use

Use only at a real decision boundary where a buried or competing constraint could change the next action, for example:

- before weakening or rewriting a test, fixture, or compatibility seam
- before widening an API, schema, dependency, permission, or write scope
- before an irreversible or shared-state mutation
- before declaring success when evidence is mixed or incomplete
- before the first consequential edit after a resume or handoff
- after repeated failures when the next attempt risks drifting from the original contract

Skip routine edits, ordinary tool calls, and already-bounded steps whose governing constraint is obvious and current.

A long conversation by itself is not a trigger. Use `context-check` for context drift, `tool-noise-guard` for repetitive tool envelopes, `verify-contract` for proof, and `handoff` for continuation state.

## Inputs

- Exact next action and target
- Current user request and project instructions
- Current task artifacts such as `SPEC.md`, `VERIFY.md`, or `HANDOFF.md` when relevant
- Directly governing code, tests, schemas, or other authoritative references
- Hard constraints, non-goals, compatibility seams, evidence, and stop conditions that can change the next action

## Workflow

1. Name the exact next action. Do not checkpoint an entire project or phase.
2. Read the smallest authoritative source set needed to govern that action.
3. Select only constraints and evidence that can change what happens next. Prefer 1-3 governing constraints.
4. Emit at most this six-line block:

```text
WORKSPACE CHECKPOINT
Action: ...
Governing constraints: ...
Current evidence: ...
Open risk: ...
Stop / escalate if: ...
```

5. If sources materially conflict, do not silently reconcile them. Stop or route to the smallest skill that can resolve the conflict, such as `mini-spec`, `scope-freeze`, or a human decision.
6. Take the named action immediately once the checkpoint is coherent.
7. Treat the checkpoint as expired when the action completes, the evidence changes, or the governing source changes. Recompute only at the next real decision boundary.

### Authority rule

A checkpoint is a working projection of live sources, not a new source of truth.

Current user instructions and current project state outrank the checkpoint. Current task artifacts outrank stale examples or prior checkpoints. If the checkpoint disagrees with a higher-authority source, discard or refresh it.

### No durable artifact by default

Do not create `WORKSPACE.md`, a checkpoint ledger, or another permanent state file merely to prove the skill ran.

Persist a constraint only when it must survive the current decision boundary. Put durable state in the artifact that already owns it: `SPEC.md`, `VERIFY.md`, `HANDOFF.md`, project instructions, or the relevant code/test contract.

## Outputs

Normally one ephemeral `WORKSPACE CHECKPOINT` block followed by the named action.

If explicitly invoked and no real decision boundary exists, output only:

```text
WORKSPACE CHECKPOINT: not needed — next action is already bounded.
```

## Stop conditions

- The exact next action is named.
- The smallest governing constraint set is active and source-backed.
- Material source conflicts are surfaced instead of silently resolved.
- The action starts immediately after the checkpoint.
- The checkpoint is not treated as durable truth after its action or evidence changes.

## Anti-patterns

- Asking the model to reveal hidden thoughts, chain-of-thought, or internal representations.
- Summarizing the whole conversation before every meaningful step.
- Running a checkpoint before every edit, tool call, test, or command.
- Inventing a constraint because it sounds prudent rather than reading an authoritative source.
- Letting a stale checkpoint outrank current code, tests, task artifacts, or user instructions.
- Creating `WORKSPACE.md` or a checkpoint ledger for routine work.
- Using the checkpoint instead of `context-check`, `verify-contract`, `ship-mini`, or `handoff`.
- Claiming this skill implements, observes, or proves a model's internal global workspace.
