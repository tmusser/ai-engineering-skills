---
name: teach-back
description: Transfer ownership of a verified implementation by testing and repairing the human's understanding of its behavior, decisions, and failure modes without turning every task into a tutorial.
---

# Teach Back

## Purpose

Turn a verified implementation into transferable human understanding.

**Transfer ownership, do not narrate the diff.** The goal is for the human to explain, debug, and safely modify the implementation rather than merely receive an agent-generated code tour.

**Test understanding, do not assume it.** Ask for a small teach-back attempt before supplying a complete explanation, then repair only material gaps using implementation evidence.

## When to use

Use after trustworthy verification when at least one learning trigger exists:

- the implementation introduced an unfamiliar technology, pattern, or dependency
- a consequential design decision or trade-off should remain human-owned
- the control flow, state transition, data path, or failure mode is non-obvious
- the human expects to review, debug, maintain, or extend the change later
- learning from the implementation is an explicit task goal

Skip boilerplate, tiny reversible patches, familiar work, and tasks where the human does not want a learning pass.

This skill is optional. A completed implementation does not require a teach-back ritual. Use `verify-contract` for correctness evidence and `handoff` for continuation state.

## Inputs

- Current task contract or `SPEC.md`
- Verified changed files or git diff
- `VERIFY.md` and relevant test evidence
- The human's stated learning goal or current familiarity when available
- Directly relevant architecture, interfaces, schemas, or runtime behavior

## Workflow

1. Confirm that implementation verification is trustworthy enough to teach from. If correctness is unresolved, stop and route to `verify-contract` or diagnosis first.
2. Confirm that a learning trigger exists. If none exists, say that `teach-back` is not needed and stop.
3. Select the smallest useful learning target:
   - one behavior path
   - no more than three consequential decisions, concepts, or failure seams
   - one likely maintenance or debugging responsibility
4. Build a compact, source-grounded implementation map. Trace the task through the changed system, for example:

   ```text
   request -> entry point -> transformation -> state or dependency -> output -> verification
   ```

   Reference the actual files, functions, tests, or observed behavior. Label claims as:
   - **Observed** — directly supported by code, tests, or verification evidence
   - **Inferred** — a plausible design intent not explicitly documented
   - **Open** — unresolved or not proven by the available evidence
5. Ask the human for a short teach-back attempt before giving the full explanation. Ask only what matters for ownership:
   - What happens from input to output?
   - Why was the consequential approach chosen?
   - Where would you investigate one concrete failure?
6. Compare the attempt with the implementation evidence. Preserve what is correct. Correct only material gaps or misconceptions, and point to the exact evidence that resolves each gap.
7. Ask one transfer question that requires prediction, debugging, or modification rather than recall. Keep it close to the completed implementation.
8. Close with a compact ownership check:
   - behavior path understood: yes / partial / no
   - main trade-off understood: yes / partial / not applicable
   - likely failure seam understood: yes / partial / no
   - remaining gap: none | describe
9. Keep the result conversational by default. Create `LEARN.md` only when the learning state must survive the session, recur across tasks, or be shared with another person.

## Outputs

Normally:

- Source-grounded implementation map
- Human teach-back attempt and targeted correction
- One transfer question
- Compact ownership check

Optionally, when durable learning state is justified:

- `LEARN.md` containing the behavior path, decisions and trade-offs, invariants, likely failure seams, demonstrated understanding, and remaining gaps

## Stop conditions

- The human can explain the behavior path and locate the main failure seam.
- The relevant trade-off is understood or explicitly marked not applicable.
- The remaining gap requires broader foundational study outside the completed implementation.
- Verification is not trustworthy enough to teach from.
- The human declines or no meaningful learning trigger exists.

## Anti-patterns

- Producing a long code walkthrough before the human attempts a teach-back.
- Treating completion of the skill as proof that learning occurred.
- Asking trivia or syntax questions that do not test maintenance, debugging, or modification ability.
- Inventing architecture or design intent that is not supported by the implementation.
- Hiding uncertainty instead of labeling observed, inferred, and open claims.
- Replacing `verify-contract` with an explanation of why the code probably works.
- Creating `LEARN.md` for every task or adding it to the starter artifact set.
- Forcing a quiz after the human declines or when speed matters more than learning.
- Asking for private chain-of-thought or hidden reasoning.
- Shaming incomplete understanding instead of repairing the smallest material gap.
