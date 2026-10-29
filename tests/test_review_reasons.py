from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "review_reasons.py"
SPEC = importlib.util.spec_from_file_location("review_reasons", MODULE)
assert SPEC is not None and SPEC.loader is not None
REASONS = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = REASONS
SPEC.loader.exec_module(REASONS)


class ReviewReasonTaxonomyTests(unittest.TestCase):
    def assert_code(self, details: str, expected: str) -> None:
        reason = REASONS.classify_review_reason(details)
        self.assertEqual(reason.code, expected)
        self.assertEqual(reason.details, details)

    def test_core_reason_codes_are_stable(self) -> None:
        cases = {
            "missing SPEC.md: SPEC.md": "SPEC_MISSING",
            "SPEC.md missing concepts: compatibility seams": "SPEC_INCOMPLETE",
            "VERIFY.md requests REVIEW_REQUIRED": "VERIFY_REVIEW_REQUESTED",
            "structured evidence JSON is invalid: Expecting value": "STRUCTURED_EVIDENCE_INVALID",
            "compatibility probes are REQUIRED but no baseline probe is recorded.": "COMPATIBILITY_UNCERTAIN",
            "verification is stale because repository state changed after the verified snapshot.": "VERIFICATION_STALE",
            "verification freshness guard unavailable: helper.py": "VERIFICATION_FRESHNESS_UNESTABLISHED",
            "ENFORCED diff budget missing field(s): max added lines": "DIFF_BUDGET_INCOMPLETE",
            "added-line budget cannot be established for binary/unmeasurable file(s): image.png": "DIFF_BUDGET_UNMEASURABLE",
            "implementation diff: 5/3 changed files, 140/120 added lines; budget exceeded: changed files 5 > 3": "DIFF_BUDGET_EXCEEDED",
            "protected path touched: src/api.py": "PROTECTED_PATH_CHANGED",
            "tests changed: tests/test_app.py": "TESTS_CHANGED",
            "fixture/data changed: data/sample.csv": "FIXTURE_DATA_CHANGED",
            "dependencies changed: pyproject.toml": "DEPENDENCIES_CHANGED",
        }
        for details, expected in cases.items():
            with self.subTest(details=details):
                self.assert_code(details, expected)

    def test_unknown_reason_is_never_dropped(self) -> None:
        reason = REASONS.classify_review_reason("new future review state")
        self.assertEqual(reason.code, "UNCLASSIFIED_REVIEW")
        self.assertEqual(reason.category, "other")

    def test_batch_classification_preserves_order(self) -> None:
        reasons = REASONS.classify_review_reasons(
            [
                "tests changed: tests/test_app.py",
                "dependencies changed: pyproject.toml",
            ]
        )
        self.assertEqual(
            [reason.code for reason in reasons],
            ["TESTS_CHANGED", "DEPENDENCIES_CHANGED"],
        )


if __name__ == "__main__":
    unittest.main()
