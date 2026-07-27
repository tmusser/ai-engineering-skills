# Workspace Checkpoint

`workspace-checkpoint` is an optional decision-boundary skill for reloading a tiny set of governing constraints immediately before a consequential action.

It is not a planning stage, a context summary, an introspection prompt, or a durable artifact.

## Why this exists

The July 2026 Transformer Circuits paper [Verbalizable Representations Form a Global Workspace in Language Models](https://transformer-circuits.pub/2026/workspace/index.html) reports evidence that modern language models maintain a small, selectively populated set of verbalizable representations used for flexible reasoning. The authors also report that explicit chain-of-thought can reduce dependence on this internal workspace by externalizing intermediate state, and that longer-timescale deliberation necessarily writes intermediate results into context and later reads them back.

This repo does **not** implement the paper's Jacobian lens, observe a model's internal J-space, or reproduce counterfactual reflection training. The paper does not prove that this skill improves coding-agent behavior.

The portable engineering hypothesis is narrower:

> At a consequential decision boundary, re-presenting only the live constraints and evidence that can change the next action may be more useful than carrying another broad summary of the whole session.

That hypothesis fits the repo's existing progressive-disclosure rule: load narrowly, expand on evidence, preserve durable state only when it buys back safety or resumability.

## Ownership boundary

`workspace-checkpoint` owns **last-mile reactivation before one consequential action**.

It does not replace nearby controls:

| Need | Owner |
| --- | --- |
| Detect context drift or durable-state gaps | `context-check` |
| Reduce repetitive tool-result carry-forward | `tool-noise-guard` |
| Define task scope and acceptance | `mini-spec` / `scope-freeze` |
| Prove the implementation | `verify-contract` |
| Check material activation risk | `ship-mini` |
| Preserve state for another session | `handoff` |
| Re-center one risky next action | `workspace-checkpoint` |

## Trigger test

Use the checkpoint only when all three are true:

1. there is a specific next action;
2. getting that action wrong could violate a live boundary; and
3. more than one current constraint, source, or piece of evidence could plausibly change the action.

Otherwise skip it.

Examples of good triggers include weakening a failing test, widening an API after repeated implementation failures, performing a shared-state mutation, declaring success with mixed evidence, or making the first consequential edit after a resume.

## Output shape

```text
WORKSPACE CHECKPOINT
Action: ...
Governing constraints: ...
Current evidence: ...
Open risk: ...
Stop / escalate if: ...
```

The checkpoint is deliberately ephemeral. Do not create `WORKSPACE.md` or a checkpoint ledger. If a constraint must survive beyond the immediate action, persist it in the artifact that already owns that state.

## Evaluation boundary

Treat this feature as a workflow hypothesis until it earns evidence in `agent-workflow-bench`.

A useful benchmark should create competing context around one hidden load-bearing constraint, then compare a strong no-skill route, the existing skill route, and the same route with a checkpoint immediately before the critical action. The evaluator should score preserved behavior and hidden-contract compliance, not whether the agent produced a checkpoint block.

Until such evidence exists, make no claim that `workspace-checkpoint` improves pass rate, reasoning quality, or model internals.
