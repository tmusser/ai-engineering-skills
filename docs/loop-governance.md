# Loop governance

Loops do not remove the engineer. They move the engineer's job from prompting each
step to defining the signal, budget, rollback, ledger, and stop condition.

A loop without a gate is automated drift.

Use loops only when the feedback is objective enough to evaluate repeated attempts.

## Loop contract

Before running repeated agent iterations, define:

- Artifact being improved:
- Feedback signal:
- Acceptance threshold:
- Budget / max iterations:
- Revert rule:
- Ledger location:
- Stop condition:
- Human review trigger:

If any field is missing, do one pass only and mark verification as
`REVIEW_REQUIRED`.

## Good loop signals

- tests passing/failing
- lint/typecheck output
- deterministic evaluator score
- benchmark metric
- golden-file diff
- explicit human review checklist

## Bad loop signals

- "make it better"
- vibes-only self-critique
- unbounded retries
- changing tests to make the loop pass
- hidden state only in chat

## Relationship to verify gates

Markdown defines the contract.
`verify_gate.py` checks cheap objective evidence.
Humans review ambiguous cases.
