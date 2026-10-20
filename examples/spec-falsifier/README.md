# Spec Falsifier: CSV Region Filter

A worked, fictional pre-implementation adversarial review. No code or real data
are involved. Both example specs intentionally meet the *structural* spec gate;
only the strengthened one closes the source-backed counterexample.

## Original request (governing intent)

> Add an optional `region` filter to the existing CSV orders export. Do not
> change the existing column names or order. When there are no matching orders,
> keep the existing header-only CSV response.

This sentence is the source for the no-match behavior. Without this request or
another authoritative source stating it, the reviewer must not invent the rule.

## Initial contract

[weak-SPEC.md](weak-SPEC.md) checks only the happy path with matching orders.
The existing `spec_gate.py` can return PASS: all required audit fields exist.
But its job is structural auditability, not judging whether all intended behavior
was captured.

## Concrete counterfeit

A plausible implementation of the weak spec:

```python
def export_orders(region):
    matching = [row for row in orders if row.region == region]
    if not matching:
        return ""  # Wrong: no CSV header on zero matches
    return render_csv(columns=EXISTING_COLUMNS, rows=matching)
```

- **Input:** `region="Antarctica"`, with no matching orders.
- **Actual counterfeit output:** empty string, not a header-only CSV.
- **Why the weak criterion still passes:** the acceptance/demo checks only
  `region="East"` with matching rows; the no-match case is unconstrained by
  its acceptance criteria and demonstration.
- **Violation:** the original request explicitly preserves the header-only
  behavior. This is a **SOURCE_BACKED** omission, not speculation.

## Spec falsification result

```text
SPEC FALSIFICATION
Verdict: FOUND
Target: weak-SPEC.md: acceptance criteria and verification demo
Counterfeit: region=Antarctica, zero matches -> empty string
Violation: loses required header-only CSV [source: Original request above]
Basis: SOURCE_BACKED [examples/spec-falsifier/README.md: Original request]
Discriminator: assert zero-match export equals header-only CSV with original column order
Proposed SPEC delta: accept the empty-region case and require that regression check
Next: revise SPEC before build-one
```

## Corrected contract

[strengthened-SPEC.md](strengthened-SPEC.md) adds a focused, observable no-match
acceptance criterion and a corresponding verification demo. It also explicitly
links to the original request rather than letting the reference disappear.

It does **not** demand an unrelated API redesign, new data schema, or broad test
suite. The counterfeit now fails the proposed discriminator without changing
the intended success path.

Run the structural check yourself:

```bash
python scripts/spec_gate.py --spec examples/spec-falsifier/weak-SPEC.md --strict-review
python scripts/spec_gate.py --spec examples/spec-falsifier/strengthened-SPEC.md --strict-review
```

Both are expected to be `PASS`; only an adversarial semantic review exposes
the original omission. This example demonstrates the skill's *reasoning pattern*,
not measured improvements in model reliability.
