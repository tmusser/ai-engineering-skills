---
name: test-mini
description: Add focused deterministic tests, fixtures, or smoke checks.
---

# Test Mini

## Purpose

Protect against wrong behavior without heavy tests.

## When to use

Use for ML model workflows, agents, dashboards, data transformations, metric calculations, scheduled jobs, and any behavior that can appear to run while being wrong.

## Inputs

- Implemented slice
- Expected behavior
- Available fixtures or examples
- Build/test/run commands
- Optional SPEC test-sensitivity contract

## Workflow

1. Add one deterministic behavior test when possible.
2. Add one fixture or golden example when useful.
3. Add one smoke test or manual verification path.
4. Run exact commands.
5. If SPEC marks `Test sensitivity requirement: REQUIRED`, run the targeted fault-injection pass described below.
6. Record command output and result.
7. Keep tests focused on the changed behavior.

## Test sensitivity pass

Use this only when SPEC explicitly requires it. The point is to prove a targeted
test is sensitive to the behavior it claims to protect, not to maximize mutation
coverage.

For each declared Sensitivity ID:

1. Start from the declared `Test command` and `Fault model`.
2. Inject one narrow fault that should violate the protected behavior.
3. Prefer a disposable worktree, scratch copy, or exact reversible local edit.
   Do not inject faults into production, shared external state, or irreversible
   data.
4. Run the exact declared targeted test command.
5. Count the fault as killed only when:
   - the command exits nonzero;
   - the failure is the expected protected-behavior assertion or signal, not a
     syntax/import/setup crash;
   - concise failure evidence is recorded.
6. Restore the implementation exactly.
7. Rerun the same targeted test command and require exit code 0.
8. Record the fault, mutated exit code, expected-failure confirmation, concise
   failure evidence, restored exit code, and restoration evidence in VERIFY.md.

A surviving fault is `REVIEW_REQUIRED`: the test may be too weak, the fault model
may be poor, or the protected behavior may not be exercised. It is not
automatically a functional failure in the implementation.

Do not broaden this into a mutation-testing campaign unless the user explicitly
asks for one.
## Test integrity

Prefer adding tests over changing existing tests.

If modifying existing tests:

1. Record the changed test path.
2. State why the old assertion was wrong or incomplete.
3. Name the source of truth.
4. Preserve the prior assertion or replace it intentionally.
5. Mark verification as `REVIEW_REQUIRED` unless the rationale is explicit.

Never weaken tests merely to match the implementation.

## Outputs

- Focused test or fixture
- Smoke path
- Exact command results
- Remaining risk notes
- Test-sensitivity evidence when SPEC requires it

## Stop conditions

- The behavior is proven enough for the task risk.
- No deterministic check is possible without changing the design.

## Anti-patterns

- Only checking that the code runs without checking correctness.
- Adding broad tests unrelated to the changed behavior.
- Hiding manual verification steps in chat.
- Counting any nonzero mutated test run as proof even when it failed for the wrong reason.
- Leaving an injected fault in the working tree after the sensitivity pass.
- Running fault injection against production or shared external state.
