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

The goal is not to preload every rule. Skills should be small, selectively loaded
interfaces for context that matters only when the task reaches that boundary.

## Context engineering for stronger models

Anthropic's July 2026 article
[The new rules of context engineering for Claude 5 generation models](https://claude.com/blog/the-new-rules-of-context-engineering-for-claude-5-generation-models)
describes a similar shift: Anthropic reports removing over 80% of Claude Code's system
prompt for newer models with no measurable loss on its coding evaluations, then recommends
more model judgment, progressive disclosure, simpler interfaces, and richer references.

This repo takes a portable version of that philosophy:

- do not turn project instructions or installed skills into one giant behavioral prompt
- load a narrow skill only when its failure mode is actually present
- prefer small interfaces and explicit states over long example-driven instructions
- prefer high-fidelity references such as tests, code, schemas, mockups, and rubrics over
  lossy prose restatements
- preserve durable state when it buys back resumability, auditability, or safety
- let ordinary low-risk work stay ordinary

This is why optional safeguards such as `analyze-mini`, `ship-mini`, `constitution-lite`,
and context controls are conditional rather than mandatory stages. Progressive disclosure
should reduce context pressure, not create a hidden token tax.

## Decision reactivation and the workspace hypothesis

The July 2026 Transformer Circuits paper
[Verbalizable Representations Form a Global Workspace in Language Models](https://transformer-circuits.pub/2026/workspace/index.html)
reports evidence that modern language models maintain a small, selectively populated set of
verbalizable representations used for flexible reasoning. The authors also report that
explicit chain-of-thought can make one reasoning benchmark more robust to workspace ablation
by externalizing intermediate state, and that longer-timescale deliberation extends itself by
writing intermediate results into context and reading them back later.

This repo does not expose that internal workspace, implement the paper's Jacobian lens, or
reproduce counterfactual reflection training. The paper also does not prove that a workflow
checkpoint improves coding-agent behavior.

`workspace-checkpoint` takes a narrower engineering hypothesis from the result: immediately
before a consequential action, reload only the current source-backed constraints and evidence
that can change that action. The checkpoint is ephemeral and should not become another durable
artifact or whole-session summary. See [Workspace Checkpoint](workspace-checkpoint.md).

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
3. High-fidelity authoritative references
4. Durable artifacts
5. Named lightweight rituals
6. Long behavioral instruction packs

More process is not better. More durable signal is better.

## Plan Mode and the practical rule

Plan Mode is useful. This repo adds an earlier question before plan approval:
is this the right bounded work? It also adds later checks for evidence and restart
state.

Use prompts for one-off direction.
Use references when existing code, tests, artifacts, or rubrics express the target more
precisely than another prose summary would.
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
