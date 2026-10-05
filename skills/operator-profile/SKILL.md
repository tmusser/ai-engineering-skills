---
name: operator-profile
description: Create a compact operator preference profile that tunes safe workflow defaults without overriding task contracts, repository instructions, safety boundaries, or required verification.
---

# Operator Profile

## Purpose

Configure how AI Engineering Skills should behave for a particular operator without
turning personal preferences into a second task contract.

Setup skill, not a workflow stage. Run it when preferences are first established or
materially change, then let other skills consume the profile as a default.

The profile may narrow authority; it may not grant new authority.

## When to use

Use when the operator wants recurring defaults for ceremony, autonomy,
verification depth, communication density, or ambiguity handling.

Do not run it for every task. Skip it when the current request already gives the
needed preferences or when no persistent personalization is useful.

## Inputs

- Explicit operator preferences
- Optional existing native user/project instructions
- Optional project-specific preferences
- Intended profile scope: session, project, or user

Do not infer durable preferences from one-off behavior, a single terse request, or
temporary task pressure.

## Authority boundary

An operator profile is a preference layer, not an authorization layer.

A current explicit instruction, repository-native instruction, task contract,
safety boundary, tool permission, scope freeze, verification requirement, or human
gate outranks a profile default when they conflict.

The profile may make behavior stricter. It must not:

- expand write scope, tool access, permissions, or side effects
- weaken required verification, compatibility probes, or review gates
- convert a human approval boundary into autonomous permission
- override a named acceptance criterion, non-goal, or repository rule
- hide material ambiguity merely because the operator prefers fewer questions

## Workflow

1. Establish the intended profile scope: `session`, `project`, or `user`.
2. Capture only these recurring defaults:
   - Ceremony preference: `lean | balanced | guarded`
   - Autonomy boundary: `propose-only | bounded-execution | human-gate-side-effects`
   - Verification depth: `targeted | standard | expanded`
   - Communication density: `lean | normal | explanatory`
   - Ambiguity handling: `ask-material | safe-reversible-assumptions`
3. Ask at most five compact questions, and only for fields that are genuinely
   unknown or materially affect the profile.
4. If a project needs a local exception, record it as a project-specific note
   rather than silently changing the broader operator default.
5. Emit one compact profile block.
6. If persistence is wanted, place the block in an existing agent-native user or
   project instruction surface, or another explicitly chosen configuration
   surface. Do not invent a second instruction hierarchy.
7. Re-run setup only when preferences materially change.

### Field semantics

Ceremony preference affects tie-breaks only after task risk is understood.
`lean` favors the smallest equally safe route. `guarded` may favor slightly more
durable evidence when two routes protect the same named risks. It never overrides
a concrete reason to use a lighter or heavier route.

Autonomy boundary is a ceiling. `bounded-execution` means the profile itself does
not add an extra approval step inside work that is already authorized; it does not
authorize tools, writes, deployment, sending, publishing, or other side effects.

Verification depth controls optional proof beyond mandatory checks. `targeted`
stops at required evidence, `standard` adds cheap relevant regression proof, and
`expanded` allows additional adjacent high-value checks when their cost is low.
Required gates remain required in every mode.

Communication density controls routine response detail only. It does not suppress
risks, blockers, uncertainty, exact commands, evidence, or decision-relevant
tradeoffs.

Ambiguity handling applies only to non-material uncertainty. Material ambiguity
that can change scope, correctness, safety, permissions, or irreversible behavior
must still be surfaced.

## Outputs

Use this compact shape:

```text
OPERATOR PROFILE
Scope: session | project | user
Ceremony preference: lean | balanced | guarded
Autonomy boundary: propose-only | bounded-execution | human-gate-side-effects
Verification depth: targeted | standard | expanded
Communication density: lean | normal | explanatory
Ambiguity handling: ask-material | safe-reversible-assumptions
Project-specific notes: none | ...
```

Do not create `OPERATOR.md` by default. Persistence belongs in an existing,
explicitly chosen instruction or configuration surface.

## Stop conditions

- Every retained field reflects an explicit operator preference.
- The precedence and authority boundary are clear.
- The profile is compact enough to remain useful as context.
- Persistence, if requested, uses an existing explicit surface.
- No task-specific requirement has been promoted into a durable preference.

## Anti-patterns

- Treating the profile as permission to perform actions the task did not authorize.
- Making the profile a required first step in every workflow.
- Creating `OPERATOR.md` automatically.
- Copying repository instructions or task acceptance criteria into the profile.
- Inferring stable preferences from one conversation.
- Using `targeted` verification to skip a required gate.
- Using `lean` ceremony to ignore a named risk.
- Using `safe-reversible-assumptions` for irreversible or contract-shaping choices.
