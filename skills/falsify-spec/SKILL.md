---
name: falsify-spec
description: Adversarially test a bounded SPEC.md for plausible wrong implementations that still pass its written acceptance criteria, then propose source-backed discriminating checks.
---

# Falsify Spec

## Purpose

Find the **plausible wrong implementation that still passes the written spec**.
Pressure-test acceptance criteria before coding, not the code after it ships.

This is an optional adversarial pass between `mini-spec` and implementation.
It does not replace source grooming, the deterministic `spec_gate.py` auditability
check, `test-mini`, or post-implementation `verify-contract`.

## When to use

Invoke as `/falsify-spec` or ask "What wrong implementation could pass this spec?"
Use selectively when a spec is written but an ambiguous boundary, regression
seam, data meaning, or potentially weak acceptance test could produce false
confidence. Skip when the slice is trivial and already unambiguous.

Do not activate merely because `mini-spec` ran or the skill is installed.
If a usable spec does not exist yet, write one with `mini-spec` first.

## Inputs

- Current `SPEC.md` with acceptance criteria, non-goals, invalid-if constraints,
  verification demo, and any declared authoritative references
- Original user request and directly relevant tests, schemas, code, or fixtures
- Named compatibility seams and any known baseline behavior

## Workflow

1. **Read authority narrowly.** Inspect `SPEC.md`, the original request, and
   only sources that govern the candidate boundary. Record discrepancies;
   source silence is not evidence of an intended requirement.
2. **Pick at most three high-consequence targets.** Prefer criteria that could
   pass shallow tests while breaking the user's intended outcome, a preserved
   behavior, or a named non-goal. Do not generate a generic test checklist.
3. **Construct a concrete counterexample.** For each target, name a plausible
   implementation, an input or state, and its observable output. Explain which
   *written* acceptance criterion/test it passes and what intended behavior it
   would violate. If it cannot plausibly pass, discard it.
4. **Classify the basis.** A counterexample is `SOURCE_BACKED` only when the
   violated expectation has a locator in the request or a governing source.
   Otherwise label it `HYPOTHESIS`, not a proven defect or new requirement.
5. **Find the smallest discriminator.** Propose one precise acceptance-criterion
   delta and, when feasible, one focused negative/regression test or manual probe
   that rejects the counterfeit while allowing valid behavior. Keep original
   source semantics, scope ceilings, permissions, and existing tests intact.
6. **Resolve ownership correctly.** For `SOURCE_BACKED` gaps, recommend updating
   the existing `SPEC.md` and proof target *before implementation*. For
   `HYPOTHESIS` gaps that require a product choice, mark `DECISION_REQUIRED`;
   do not silently turn them into acceptance criteria.
7. **Stop.** Report at most three counterexamples in a single compact response.
   If explicitly authorized, amend the existing spec; otherwise propose the
   exact delta for the operator to accept. Do not create `FALSIFICATION.md`,
   a second contract, or a mandatory new workflow stage.

## Outputs

Use this compact shape; omit empty entries:

```text
SPEC FALSIFICATION
Verdict: FOUND | DECISION_REQUIRED | NONE_FOUND
Target: [criterion or referenced source]
Counterfeit: [specific input -> behavior that could pass the written check]
Violation: [what goes wrong and where the expectation is sourced]
Basis: SOURCE_BACKED [locator] | HYPOTHESIS [open decision]
Discriminator: [smallest test or observation rejecting the counterfeit]
Proposed SPEC delta: [one bounded change, or decision required]
Next: revise SPEC | ask owner | proceed to implementation
```

`FOUND` means at least one source-backed loophole survived the current spec
and proof. `DECISION_REQUIRED` means a plausible loophole needs an owner choice
before it may become a contract. `NONE_FOUND` means this bounded search found
none; **it does not prove the spec is complete**.

## Stop conditions

- Each retained counterexample could actually pass the written check.
- Every proposed mandatory change is source-backed; unresolved product choices
  remain explicit rather than silently resolved.
- A focused discriminator and next owner action are clear, or no plausible
  counterexample was found within the three-target budget.

## Anti-patterns

- Inventing feature requirements or product behavior to make an attack dramatic.
- Claiming a speculative edge case is a proven spec defect.
- Rewriting authoritative references into a weaker duplicate spec.
- Asking for broad new tests unrelated to a specific counterfeit.
- Running code changes or post-implementation verification during this pass.
- Treating a `spec_gate.py` PASS as semantic correctness—or this pass as proof.
- Requiring falsification on every small task or growing a separate artifact ledger.
