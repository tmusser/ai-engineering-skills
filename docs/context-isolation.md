# Route-First Context Isolation

Coding agents should begin with the smallest instruction and project context set that
can safely execute the current task.

This is a loading rule, not a prohibition on discovery. An agent may inspect more of
the repository when evidence shows the task crosses a boundary or the selected context
is insufficient.

## Default rule

```text
Resolve the route.
Load the selected skills and directly relevant project state.
Load nothing else by default.
Expand only when the task or evidence requires it.
```

The goal is to preserve working-context headroom and reduce instruction collisions. It
is not to make the agent blind to dependencies or neighboring behavior.

## Startup sequence

1. Identify the concrete task and proof target.
2. Select the smallest workflow route that protects the named risk.
3. Load only the skills used by that route.
4. Load current-state artifacts such as `SPEC.md`, `VERIFY.md`, or `HANDOFF.md` when
   they are relevant.
5. Load the directly implicated code, tests, configuration, and local guidance.
6. Start the next safe action.

Do not preload the full skill pack simply because it is installed.

## Expansion triggers

Expand context when:

- the task genuinely spans several skills or subsystems
- a named compatibility seam leads into another file or module
- verification fails and identifies a missing dependency or assumption
- current-state artifacts reference an unresolved decision elsewhere
- a repository-level instruction explicitly requires broader inspection

When expanding, add the smallest missing source first. Do not respond to one missing
fact by loading the entire repository narrative.

## Discovery versus authority

Context isolation limits the default working set. It does not freeze read scope.

- Searches and reads remain available unless explicitly forbidden.
- Current task artifacts outrank templates and examples.
- Project-specific instructions outrank generic skill guidance.
- Omitted context is unknown, not irrelevant.
- An agent should name material uncertainty rather than infer unseen behavior.

## Multi-skill tasks

Some tasks legitimately need several skills. Keep the route explicit:

```text
mini-spec -> scope-freeze -> build-one -> verify-contract
```

Load those skills and the relevant task artifacts. Do not also load unrelated analysis,
shipping, debugging, and handoff skills unless the task reaches those gates.

## Failure modes this avoids

- conflicting instructions from unrelated skills
- stale examples outranking live project state
- long prompts hiding the actual acceptance criterion
- accidental escalation into a larger workflow
- spending context budget on process that the task does not need

## Failure modes this must not create

- refusing necessary repository discovery
- ignoring adjacent compatibility seams
- treating a narrow initial load as proof that the task is narrow
- omitting verification because its skill was not loaded at startup
- continuing with known missing context instead of expanding deliberately

## Relationship to context hydration

Context hydration can implement this rule by selecting a compact packet after the route
is known. Hydration remains optional. A human or agent can follow the same discipline
with ordinary file reads.

The portable principle is the important part: **route first, load narrowly, expand on
evidence**.
