# REVIEW_REQUIRED Reason Taxonomy

`REVIEW_REQUIRED` is intentionally distinct from `FAIL`: the observed behavior
may still be correct, but the available evidence or change-control state is not
strong enough for an unqualified `PASS`.

A single generic review bucket is useful for gate severity but weak for routing.
`scripts/verify_gate.py` therefore emits stable reason codes alongside the
existing human-readable `review_required` messages.

## Output contract

Text output keeps the existing review messages and adds codes:

```text
Review required:
- tests changed: tests/test_export.py

Review reason codes:
- [TESTS_CHANGED] change_control: tests changed: tests/test_export.py
```

JSON output keeps the legacy `review_required` array and adds
`review_reasons`:

```json
{
  "status": "REVIEW_REQUIRED",
  "review_required": [
    "tests changed: tests/test_export.py"
  ],
  "review_reasons": [
    {
      "code": "TESTS_CHANGED",
      "category": "change_control",
      "details": "tests changed: tests/test_export.py"
    }
  ]
}
```

The old prose field remains for compatibility. New tooling should prefer the
stable `code` for routing and retain `details` for humans.

## Stable codes

| Code | Category | Meaning |
| --- | --- | --- |
| `SPEC_MISSING` | contract | Required SPEC artifact is missing. |
| `SPEC_INCOMPLETE` | contract | SPEC exists but required verification concepts are incomplete. |
| `VERIFY_REVIEW_REQUESTED` | evidence | VERIFY.md itself records `REVIEW_REQUIRED`. |
| `STRUCTURED_EVIDENCE_INVALID` | evidence | Machine-readable verification evidence is malformed, incomplete, contradictory, or explicitly review-required. |
| `COMPATIBILITY_UNCERTAIN` | compatibility | Required compatibility baseline/post-change proof is incomplete or unresolved. |
| `VERIFICATION_STALE` | freshness | Verification evidence was valid for an older repository snapshot. |
| `VERIFICATION_FRESHNESS_UNESTABLISHED` | freshness | Freshness cannot be established safely. |
| `DIFF_BUDGET_INCOMPLETE` | change_control | An enforced diff-budget contract is incomplete. |
| `DIFF_BUDGET_UNMEASURABLE` | change_control | The added-line budget cannot be measured reliably. |
| `DIFF_BUDGET_EXCEEDED` | change_control | The implementation exceeded the accepted patch-size tripwire. |
| `PROTECTED_PATH_CHANGED` | change_control | A protected path changed and requires review. |
| `TESTS_CHANGED` | change_control | Test files changed and require integrity review. |
| `FIXTURE_DATA_CHANGED` | change_control | Fixture or source-data files changed and require review. |
| `DEPENDENCIES_CHANGED` | dependency | Dependency declarations or lockfiles changed. |
| `TEST_SENSITIVITY_SURVIVED` | test_integrity | A declared fault survived the targeted test or failed for the wrong reason. |
| `TEST_SENSITIVITY_UNESTABLISHED` | test_integrity | Required test-sensitivity evidence is missing or incomplete. |
| `UNCLASSIFIED_REVIEW` | other | A future/unknown review reason was preserved but has no dedicated code yet. |

`UNCLASSIFIED_REVIEW` is intentional fail-visible behavior. New review states
must not silently disappear merely because the taxonomy has not been extended yet.

## Severity does not come from the code

Reason codes do not change the top-level gate decision.

For example:

- `TESTS_CHANGED` is still `REVIEW_REQUIRED`, not `FAIL`;
- `DIFF_BUDGET_EXCEEDED` is still `REVIEW_REQUIRED`;
- a failed compatibility probe remains `FAIL` and therefore does not need a
  review-reason code to preserve its severity.

The taxonomy explains *why review is required*. It is not a second status system.

## Downstream use

The PR evidence renderer surfaces deterministic reason codes in its evidence
state when available.

`scripts/workflow_doctor.py` also forwards reason codes from the verify gate in
text and JSON output. This lets local tooling or agents distinguish, for example:

- rerun verification for `VERIFICATION_STALE`;
- inspect test intent for `TESTS_CHANGED`;
- revisit the accepted slice for `DIFF_BUDGET_EXCEEDED`;
- resolve compatibility evidence for `COMPATIBILITY_UNCERTAIN`.

Those are routing hints, not automatic remediation authority.

## Compatibility

Existing consumers of `review_required` continue to work because that field is
unchanged.

Consumers that parse the complete JSON object by exact key set must allow the new
`review_reasons` field.

## Claim boundary

A reason code classifies an observed deterministic review condition. It does not
prove the condition is important, harmless, correctly resolved, or sufficient to
describe every human concern with the change.
