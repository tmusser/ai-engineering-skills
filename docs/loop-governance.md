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

## Retry discipline

A first bounded diagnosis does not require a new ledger. Before the second repair
attempt, record the initial attempt so it counts toward the budget, fix the
contract above, and record a loop ID, input and evaluator
identities, and a consecutive no-progress limit. Choose finite limits appropriate
to the task; two no-progress attempts and three total attempts are a small debugging
example, not universal defaults. Add wall-time or cost ceilings when those matter;
the caller must enforce them before starting another attempt.

An attempt starts when a hypothesis-driven repair or evaluation starts, not only
when its command succeeds. Log tool errors and interruptions too. Each entry needs
an attempt number, active hypothesis, artifact state, evidence reference, and
outcome. Evidence should explain what changed and what the next attempt will test.

- `improved`: objective progress, but acceptance has not been established.
- `unchanged`, `regressed`, `error`: consume the consecutive no-progress budget.
- `interrupted`: stop and reconcile the actual state and any external effects.
- `accepted`: stop iterating and run the independent completion verification.

Improvement resets only the consecutive no-progress counter. Every started attempt
consumes the total budget. Stop when either limit is reached. A retry needs an
evidence-supported hypothesis; "try harder" is not one.

Keep the best known state separately from the latest attempt. Preserve failed
attempt evidence before reverting only the changes owned by that attempt. A
rollback must not discard unrelated user edits. External actions require their
own reconciliation or compensation; retry budget is not permission to repeat them.

Do not weaken tests, alter the evaluator, widen scope, or raise limits to rescue a
failing loop. A necessary change requires an explicit contract revision and fresh
verification. Keep the old ledger and the reason for revision; never rewrite the
history to appear compliant.

## Resume without resetting

The same task carries the same loop ID, consumed budget, evaluator/input identities,
and stop reason across sessions, agents, or subtasks. Use the optional loop state
in [HANDOFF.md](../templates/HANDOFF.md) to point to the ledger and best known state.
Reconcile live state before another attempt. An interrupted attempt remains spent;
record its reconciled outcome and evidence without deleting or renumbering it.
A spent budget requires an explicit revision, not a fresh chat.

## Optional deterministic retry check

For repeated work that benefits from a machine-readable record, use
[`examples/bounded-loop.json`](../examples/bounded-loop.json) as a small example:

```bash
python scripts/aes.py loop examples/bounded-loop.json
```

The example records one unsuccessful repair with diagnostic progress. The checker
returns `PASS` with `CONTINUE`: the recorded limits allow one more attempt. It does
not run that attempt. You can also invoke `python scripts/loop_gate.py <record.json>`.
Paths are relative to the caller's working directory.

The JSON record is the contract and ordered ledger in one file:

| Field | Meaning |
| ----- | ------- |
| `version` | Schema version, currently integer `1`. |
| `loop_id`, `artifact` | Stable loop identity and artifact being improved. |
| `input_id`, `evaluator_id` | Frozen task-input and evaluation-rule identities; use content hashes or immutable revisions where possible. |
| `feedback_signal`, `acceptance_threshold` | Objective observation and required result. |
| `max_attempts`, `max_stalled` | Positive integer total and consecutive no-progress limits. |
| `revert_rule`, `human_review_trigger` | Recovery boundary and conditions requiring review. |
| `review_required` | Explicit boolean; true stops regardless of apparent acceptance. |
| `attempts` | Complete ordered list; empty before the first attempt. |

Each attempt has contiguous integer `number` starting at 1, `hypothesis`,
`artifact_state`, `evidence`, matching `input_id` and `evaluator_id`, and one of the
six outcomes above. Artifact state identifies that candidate's content, including
uncommitted changes; task-input identity excludes the artifact deliberately being
improved. Evidence can reference a log, but must remain inspectable by the verifier.

| Status | Decision | Exit | Meaning |
| ------ | -------- | ---- | ------- |
| `PASS` | `CONTINUE` | 0 | Recorded limits permit one attempt; existing scope, permissions, and other ceilings still apply. |
| `PASS` | `VERIFY` | 0 | Acceptance reported; stop repair and run completion verification. |
| `FAIL` | `STOP` | 1 | Budget exhausted, progress stalled, or the ledger continued past a stop boundary. |
| `REVIEW_REQUIRED` | `STOP` | 2 | Incomplete/malformed state, stale identities, interruption, or unresolved review trigger. |

**Do not use exit 0 alone as a retry condition.** Consumers must inspect `decision`;
`VERIFY` is terminal for repair. Acceptance on the final permitted attempt is valid,
but acceptance after a prior stop boundary is not.

This read-only checker validates reported state. It does not run commands, verify
log contents, hash the workspace, authenticate a ledger, enforce wall-time/cost
ceilings, or detect deleted history and fabricated outcomes. The caller owns those
checks and must record a started attempt as `interrupted` before executing it,
then update that entry with its observed outcome. Use a single writer; this is not
a concurrent scheduler. A loop `PASS` never substitutes for `verify_gate.py` or
independent review of the original failing case and compatibility evidence.
