from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "verification_evidence.py"
SPEC = importlib.util.spec_from_file_location("verification_evidence", MODULE)
assert SPEC is not None and SPEC.loader is not None
EVIDENCE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = EVIDENCE
SPEC.loader.exec_module(EVIDENCE)


def verify_with(payload: str) -> str:
    return f"""# Verify

## Structured verification evidence

```json
{payload}
```
"""


class StructuredVerificationEvidenceTests(unittest.TestCase):
    def test_absent_block_is_legacy_compatible(self) -> None:
        parsed = EVIDENCE.parse_structured_evidence("# Verify\n")
        self.assertFalse(parsed.present)
        self.assertEqual(parsed.errors, ())

    def test_valid_command_record_parses(self) -> None:
        parsed = EVIDENCE.parse_structured_evidence(
            verify_with(
                """{
  "schema_version": 1,
  "checks": [
    {
      "check": "unit-tests",
      "command": "python -m unittest",
      "exit_code": 0,
      "evidence_source": "command",
      "status": "PASS",
      "evidence": "12 tests passed",
      "recorded_at": "2026-10-06T10:00:00Z",
      "commit": "abc123"
    }
  ]
}"""
            )
        )
        self.assertTrue(parsed.present)
        self.assertEqual(parsed.errors, ())
        self.assertEqual(parsed.checks[0]["check"], "unit-tests")

    def test_pass_command_with_nonzero_exit_is_invalid(self) -> None:
        parsed = EVIDENCE.parse_structured_evidence(
            verify_with(
                """{
  "schema_version": 1,
  "checks": [
    {
      "check": "tests",
      "command": "pytest",
      "exit_code": 1,
      "evidence_source": "command",
      "status": "PASS",
      "evidence": "claimed pass",
      "commit": "abc123"
    }
  ]
}"""
            )
        )
        self.assertIn("PASS command evidence must have exit_code 0", " ".join(parsed.errors))

    def test_requires_provenance_anchor(self) -> None:
        parsed = EVIDENCE.parse_structured_evidence(
            verify_with(
                """{
  "schema_version": 1,
  "checks": [
    {
      "check": "manual-review",
      "command": null,
      "exit_code": null,
      "evidence_source": "manual",
      "status": "PASS",
      "evidence": "reviewed output"
    }
  ]
}"""
            )
        )
        self.assertIn("requires recorded_at or commit provenance", " ".join(parsed.errors))

    def test_duplicate_check_ids_are_invalid(self) -> None:
        payload = """{
  "schema_version": 1,
  "checks": [
    {
      "check": "tests",
      "command": "pytest",
      "exit_code": 0,
      "evidence_source": "command",
      "status": "PASS",
      "evidence": "pass",
      "commit": "abc123"
    },
    {
      "check": "tests",
      "command": "pytest tests/unit",
      "exit_code": 0,
      "evidence_source": "command",
      "status": "PASS",
      "evidence": "pass",
      "commit": "abc123"
    }
  ]
}"""
        parsed = EVIDENCE.parse_structured_evidence(verify_with(payload))
        self.assertIn("duplicate check id: tests", parsed.errors)


if __name__ == "__main__":
    unittest.main()
