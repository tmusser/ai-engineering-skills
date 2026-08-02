# Workflow Route Contracts

The workflow route contract suite makes the repository's smallest-safe-route claim executable.

It is intentionally a finite conformance suite, not a runtime router. It does not infer risk from task prose, choose a workflow for an agent, or replace `ceremony-budget`. Each scenario declares its risks and proposed route; the checker verifies that the declaration obeys the repository's stable routing boundaries.

## What the checker proves

For each golden scenario, `scripts/check_route_contracts.py` checks that:

- the expected Level 0-3 route is the smallest level justified by the declared risks;
- the route includes the minimum skills and proof guards for that level;
- every declared risk has a concrete skill or proof guard covering it;
- conditional skills such as `handoff`, `ship-mini`, `analyze-mini`, `workspace-checkpoint`, and `teach-back` have an explicit trigger;
- an already-prescriptive wrapper does not receive a second ceremony contract or routing artifact;
- selected and forbidden skills do not conflict.

The checker does not claim that the scenario's risk declaration is objectively correct. Human judgment still owns that classification. The executable contract begins after the risks are named.

## Run it

```bash
python scripts/check_route_contracts.py
python -m unittest discover tests -p 'test_route_contracts.py'
```

Machine-readable output is available for CI or downstream inspection:

```bash
python scripts/check_route_contracts.py --json
```

## Scenario shape

Golden scenarios live in `tests/fixtures/workflow_route_contracts.json`.

```json
{
  "id": "bounded-parser-compatibility",
  "summary": "A bounded parser change preserves a named compatibility seam.",
  "route_explicit": false,
  "expected_level": 1,
  "risks": ["behavior_change", "scope_drift", "compatibility_seam"],
  "selected_skills": ["build-one"],
  "proof_guards": [
    "inline-boundary",
    "targeted-verification",
    "compatibility-regression-check"
  ],
  "forbidden_skills": ["mini-spec", "thin-plan", "verify-contract", "handoff"]
}
```

This example preserves the compatibility reserve without escalating a bounded, low-ambiguity change to Level 2.

## Adding a scenario

Add a scenario when it protects a distinct routing boundary, not merely another task theme.

A useful scenario should expose at least one of these questions:

- Would a lighter level leave a named risk uncovered?
- Would a heavier level add process without buying back safety?
- Is a conditional skill being invoked without its trigger?
- Is a cheap compatibility or test-integrity check being dropped from a light route?
- Is an explicit wrapper receiving a duplicate workflow contract?

Then add or extend a focused mutation test proving that the checker fails when that boundary is violated. Avoid full-text snapshots and avoid turning the fixture into a general workflow ontology.

## Claim boundary

Passing scenarios show that the repository's declared route contracts are internally consistent and regression-tested. They do not prove that an agent will classify every real task correctly, follow the selected route, or produce a correct implementation.
