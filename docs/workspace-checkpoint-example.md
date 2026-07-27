# Workspace Checkpoint Example

A focused example of the decision boundary this skill is meant to protect.

## Situation

A compatibility test fails after an implementation change. The agent has already tried two production-code fixes and is considering changing the test.

Current sources say:

- `SPEC.md`: preserve the existing public JSON shape.
- `tests/test_export.py`: locks the legacy JSON output.
- Current failure: the new CSV path accidentally changed the JSON serializer.

## Checkpoint

```text
WORKSPACE CHECKPOINT
Action: decide whether to change tests/test_export.py or repair the serializer
Governing constraints: preserve existing JSON behavior; tests are evidence unless explicitly in scope
Current evidence: CSV works, but the legacy JSON compatibility test now fails
Open risk: changing the test would hide a compatibility regression
Stop / escalate if: preserving JSON requires behavior outside the current spec ceiling
```

Next action: repair the serializer, then rerun the focused compatibility test.

## What this example does not do

It does not ask the model to describe hidden reasoning. It does not summarize the full session. It does not persist a checkpoint ledger. The block exists only to re-present the live constraints immediately before a consequential choice.
