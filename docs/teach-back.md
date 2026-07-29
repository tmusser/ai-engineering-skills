# Teach Back

`teach-back` is an optional post-verification skill for transferring ownership of an implementation back to the human who delegated it.

It is not a correctness gate, a mandatory tutorial, or another durable workflow artifact.

## Why this exists

AI-assisted implementation can produce a verified change while leaving the human unable to explain, debug, or safely modify it. That creates understanding debt even when the task itself succeeds.

The narrow workflow hypothesis is:

> A small, implementation-grounded teach-back can preserve human ownership better than an agent-generated explanation alone.

The skill tests that hypothesis by asking the human to explain the behavior path, consequential trade-off, and likely failure seam before the agent fills in missing details.

## Ownership boundary

`teach-back` owns **human understanding transfer after trustworthy verification**.

It does not replace nearby controls:

| Need | Owner |
| --- | --- |
| Define behavior and acceptance | `mini-spec` |
| Constrain the implementation slice | `scope-freeze` |
| Implement the bounded change | `build-one` |
| Prove the implementation | `test-mini` / `verify-contract` |
| Transfer implementation understanding | `teach-back` |
| Preserve continuation state | `handoff` |

The normal optional route is:

```text
build-one -> verify-contract -> teach-back -> handoff
```

Skip `teach-back` when no meaningful learning trigger exists. Skip `handoff` when no later session or agent needs continuation state.

## Trigger test

Use the skill when all three are true:

1. the implementation is verified well enough to teach from;
2. the human will benefit from understanding a non-obvious behavior, decision, or failure seam; and
3. the learning pass is worth the added interaction cost.

Good triggers include unfamiliar dependencies, consequential architectural choices, subtle data flow, non-obvious state transitions, or code the human expects to maintain.

Poor triggers include boilerplate, familiar patterns, tiny reversible patches, and urgent work where the human explicitly prefers speed over learning.

## Interaction shape

The skill should remain small:

1. trace one behavior path through actual code and tests;
2. surface no more than three consequential concepts or decisions;
3. ask the human to explain the implementation before revealing the complete explanation;
4. repair only material gaps with exact source evidence;
5. ask one prediction, debugging, or modification question;
6. stop.

The agent should distinguish direct evidence from inferred design intent and unresolved questions. A plausible explanation is not a substitute for evidence.

## Artifact policy

Do not add `LEARN.md` to the default artifact chain.

Create it only when learning state must survive the current session, recur across future tasks, or be shared with another person. A durable note should stay compact:

```markdown
# Implementation Learning Note

## Behavior path

## Decisions and trade-offs

## Invariants

## Likely failure seams

## Demonstrated understanding

## Remaining gaps

## Transfer exercise
```

Otherwise keep the teach-back conversational.

## Evaluation boundary

Treat `teach-back` as an experimental workflow hypothesis until it earns evidence.

A useful evaluation should compare at least:

- verified implementation with no learning pass;
- explanation-only review;
- generation followed by grounded teach-back and one transfer question.

The evaluator should measure whether the human can later explain, debug, or modify the implementation. It should not score whether the agent produced a polished explanation or a `LEARN.md` file.

Until such evidence exists, do not claim that the skill improves long-term retention, debugging performance, or engineering ability.
