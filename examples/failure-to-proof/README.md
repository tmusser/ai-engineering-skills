# Failure-to-Proof: A Passing Suite With Missing Evidence

A tiny, reproducible before/after demonstration of **evidence completeness**.
The original CSV implementation has a real empty-result defect, but its
happy-path test passes. The existing AES acceptance-to-evidence checker spots
that the declared empty-result requirement has no linked test record.

**No model, API key, dependency installation, or external service required.**
Python's standard library is sufficient.

## Run the crash test

From the repository root:

```bash
python examples/failure-to-proof/run_demo.py
```

For machine-readable output:

```bash
python examples/failure-to-proof/run_demo.py --format json
```

The runner executes the suites and contract probes, generates schema-v1
verification records from **actual subprocess exit codes**, and invokes the
existing `scripts/acceptance_coverage.py` CLI for each state. It uses a
temporary directory for verification artifacts. It does not call any model,
edit tracked files, or publish results.

## The two states

| Check | Before: incomplete | After: repaired |
| --- | --- | --- |
| Normal export unit suite | PASS (1 test) | PASS (2 tests) |
| Empty-result behavioral probe | FAIL (missing header) | PASS |
| `AC-1`: original CSV schema | LINKED | LINKED |
| `AC-2`: empty-result header | MISSING | LINKED |
| Acceptance coverage verdict | REVIEW_REQUIRED | PASS |

These are **expected fixture outcomes**, asserted by the runner and CI.
They are not measurements of real-world agent reliability.

The missing contract is simple: when no rows match the requested region,
the exporter must return `order_id,region` followed by a newline, not
an empty string. The baseline's only test exercises a matching row.
The repaired implementation always writes the header, and a new test explicitly
covers zero matching rows.

## Inspect the artifacts

- [SPEC.md](SPEC.md) declares both acceptance criteria with stable IDs.
- [before/export.py](before/export.py) contains the intentionally broken branch.
- [before/test_export.py](before/test_export.py) covers only the happy path.
- [after/export.py](after/export.py) removes the broken branch.
- [after/test_export.py](after/test_export.py) adds the missing test.
- [run_demo.py](run_demo.py) executes the tests, constructs evidence records,
  checks coverage, and enforces the expected before/after outcomes.

The repository-wide tests include a regression harness that verifies the demo
fails if the before bug disappears, the repaired regression test is dropped,
or the SPEC acceptance criterion is silently removed. CI also runs the demo
as an explicit independent step.

## What this proves—and doesn't

**Proves for this deterministic fixture:** a passing test suite can omit
behavior required by a spec; the existing acceptance-coverage gate identifies
the *missing linked evidence* as `REVIEW_REQUIRED`; adding a targeted
test makes that gap visible and repairable. A separately executed behavior
probe demonstrates the functional bug.

**Does not prove:** the gate discovers unknown behavioral bugs, that linking a
test proves semantic correctness, that a code-generating agent would find or
fix this bug, or that AES raises agent pass rates. Even the repaired coverage
verdict proves linkage to recorded evidence, not exhaustive test quality.

This is a reproducible **product demonstration**, not a controlled benchmark.
For empirical agent comparisons see
[benchmark findings](../../docs/benchmark-findings.md).

## Next experiment

Once this walkthrough is stable, run a controlled comparison with independent
agents, matched tasks, seeds, budgets, and hidden tests using
`agent-workflow-bench`. Report functional correctness separately from
coverage and evidence integrity, including negative or inconclusive findings.
