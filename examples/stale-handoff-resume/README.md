# Stale Handoff Resume Demo

A handoff can be detailed, internally coherent, and wrong.

This runnable case study shows why `HANDOFF.md` must not silently outrank live
repository state during resume.

## Scenario

The first session leaves a stamped handoff saying:

```text
Next task: add prefix validation to normalize_customer_id
```

After that snapshot, the live repository replaces `normalize_customer_id` with a
validated `parse_customer_id` API and deliberately removes the legacy function.
The handoff is now stale, even though its instruction still sounds plausible.

The demo forks that same stale repository into two resume paths.

### Naive path

The resumed worker trusts the handoff without checking live state. It adds prefix
validation to the function named in the handoff, resurrecting an API that the live
repository intentionally removed. The current tests fail.

### Guarded path

The resumed worker runs the bundled handoff freshness guard before editing. The
guard returns `STALE`, the edit is blocked, and the current tests remain green.

## Run it

From the repository root:

```bash
python examples/stale-handoff-resume/run_demo.py
```

Expected summary:

```text
NAIVE TESTS: FAIL
HANDOFF FRESHNESS: STALE
EDIT BLOCKED: yes
GUARDED TESTS: PASS
DEMO RESULT: PASS
```

The repository-wide runnable example command discovers the assertion suite under
`after/` automatically:

```bash
python scripts/run_runnable_examples.py
```

## What this proves

This example proves a narrow mechanism claim:

- a stamped handoff becomes stale when non-handoff repository state changes;
- blindly applying stale continuation state can damage live code;
- freshness checking can stop the edit before it happens;
- guarded resume preserves the already-green live state.

It does not prove that every stale handoff would cause damage, that freshness
checking resolves semantic conflicts automatically, or that an agent will always
reconcile live state correctly after receiving `STALE`. The required next move is
still human or agent review of the current repository before regenerating the
handoff.

## Files

- `run_demo.py` creates isolated temporary Git repositories and executes both paths.
- `after/test_demo.py` locks the expected failure and guarded outcomes.
- `skills/handoff/scripts/handoff_freshness.py` is the production guard exercised
  by the demo; the example does not reimplement it.
