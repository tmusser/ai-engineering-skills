# Operator Profile

`operator-profile` is an optional setup skill for people who want the same AI
Engineering Skills install to feel different for different operators without
forking the skills.

It is not a workflow stage. Run it once when preferences are established, then
again only when they materially change.

## What it captures

The profile records five defaults plus its scope:

- ceremony preference: `lean | balanced | guarded`
- autonomy boundary: `propose-only | bounded-execution | human-gate-side-effects`
- verification depth: `targeted | standard | expanded`
- communication density: `lean | normal | explanatory`
- ambiguity handling: `ask-material | safe-reversible-assumptions`
- scope: `session | project | user`

These are defaults, not permissions.

## Authority rule

The profile can choose among already-safe options or make behavior stricter. It
cannot expand scope, grant tool permissions, authorize side effects, weaken
verification, bypass compatibility probes, remove human gates, or override the
current task or repository instructions.

A useful shorthand is:

> Preferences tune defaults. Contracts and permissions still win.

## Persistence

The skill emits an `OPERATOR PROFILE` block. If you want it to persist, put that
block in an existing agent-native user or project instruction surface, or another
configuration surface you deliberately choose.

Do not create `OPERATOR.md` by default. The repo avoids inventing a second
instruction hierarchy just to store preferences.

A session-scoped profile can stay in conversation context. A project-scoped
profile belongs with project instructions. A user-scoped profile belongs with the
agent's user-level instruction mechanism when one exists.

## How skills consume it

`ceremony-budget` uses ceremony preference only as a tie-breaker after actual
risk is understood.

`lean-mode` may use communication density as its default for routine responses,
while still expanding when nuance or correctness requires it.

`verify-contract` uses verification depth only for optional proof beyond required
checks. Required gates and compatibility probes remain mandatory.

`ship-mini` treats the autonomy boundary as a ceiling. A profile can require
human approval earlier; it cannot create permission to activate side effects.

Clarification flows may use ambiguity handling for reversible, non-material
assumptions. Material ambiguity still has to be surfaced.

## Example

```text
OPERATOR PROFILE
Scope: user
Ceremony preference: lean
Autonomy boundary: bounded-execution
Verification depth: standard
Communication density: lean
Ambiguity handling: safe-reversible-assumptions
Project-specific notes: none
```

That profile says: prefer low ceremony and concise routine updates, execute inside
already-authorized bounded work, keep normal cheap regression proof, and avoid
interrupting for reversible low-stakes assumptions. It does not authorize writes,
deployments, or external side effects by itself.

## Install

Claude Code:

```bash
./install.sh --claude-user --only operator-profile
```

Codex CLI:

```bash
./install.sh --codex-user --only operator-profile
```

Then ask the agent:

```text
Use operator-profile to set my recurring workflow defaults.
```

The skill is intentionally excluded from normal workflow bundles because setup is
not another step to run on each task.
