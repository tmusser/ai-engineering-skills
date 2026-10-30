from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "test_sensitivity.py"
SPEC = importlib.util.spec_from_file_location("test_sensitivity", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
SENSITIVITY = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = SENSITIVITY
SPEC.loader.exec_module(SENSITIVITY)


SPEC_REQUIRED = """# Spec

## Test sensitivity gate

Test sensitivity requirement: REQUIRED

- Sensitivity ID: empty-export
  - Protected behavior: empty results return a header-only CSV
  - Test command: python -m pytest tests/test_export.py -k empty
  - Fault model: make empty results emit one body row
"""

VERIFY_KILLED = """# Verify

## Test sensitivity evidence

- Sensitivity ID: empty-export
  - Fault injected: empty branch emits one synthetic body row
  - Mutated command: python -m pytest tests/test_export.py -k empty
  - Mutated exit code: 1
  - Expected failure observed: yes
  - Failure evidence: assertion expected header-only output but observed one row
  - Restored exit code: 0
  - Restoration evidence: same targeted test passes after restoring implementation
"""


class TestSensitivityTests(unittest.TestCase):
    def test_legacy_spec_is_not_applicable(self) -> None:
        result = SENSITIVITY.evaluate("# Spec\n", "# Verify\n")
        self.assertFalse(result.active)
        self.assertEqual(result.status, "NOT_APPLICABLE")

    def test_optional_template_heading_is_supported(self) -> None:
        spec = SPEC_REQUIRED.replace(
            "## Test sensitivity gate",
            "## Test sensitivity gate (optional)",
        )
        result = SENSITIVITY.evaluate(spec, VERIFY_KILLED)
        self.assertEqual(result.status, "PASS")

    def test_explicit_not_applicable_is_compatible(self) -> None:
        spec = """# Spec

## Test sensitivity gate

Test sensitivity requirement: NOT_APPLICABLE
"""
        result = SENSITIVITY.evaluate(spec, None)
        self.assertEqual(result.status, "NOT_APPLICABLE")

    def test_required_killed_fault_and_restoration_pass(self) -> None:
        result = SENSITIVITY.evaluate(SPEC_REQUIRED, VERIFY_KILLED)
        self.assertTrue(result.active)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(result.records[0].mutated_exit_code, 1)
        self.assertTrue(result.records[0].expected_failure_observed)
        self.assertEqual(result.records[0].restored_exit_code, 0)

    def test_missing_evidence_requires_review(self) -> None:
        result = SENSITIVITY.evaluate(SPEC_REQUIRED, "# Verify\n")
        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertIn("missing test-sensitivity evidence", result.review_required[0])

    def test_duplicate_and_undeclared_ids_require_review(self) -> None:
        verify = VERIFY_KILLED + """
- Sensitivity ID: empty-export
  - Fault injected: duplicate
  - Mutated command: python -m pytest tests/test_export.py -k empty
  - Mutated exit code: 1
  - Expected failure observed: yes
  - Failure evidence: duplicate
  - Restored exit code: 0
  - Restoration evidence: restored

- Sensitivity ID: surprise
  - Fault injected: unrelated
  - Mutated command: pytest x
  - Mutated exit code: 1
  - Expected failure observed: yes
  - Failure evidence: failed
  - Restored exit code: 0
  - Restoration evidence: restored
"""
        result = SENSITIVITY.evaluate(SPEC_REQUIRED, verify)
        self.assertEqual(result.status, "REVIEW_REQUIRED")
        joined = "\n".join(result.review_required)
        self.assertIn("duplicate verification Sensitivity ID", joined)
        self.assertIn("undeclared Sensitivity ID", joined)

    def test_mutated_command_must_match_declared_test(self) -> None:
        verify = VERIFY_KILLED.replace(
            "python -m pytest tests/test_export.py -k empty",
            "python -m pytest tests/test_export.py",
        )
        result = SENSITIVITY.evaluate(SPEC_REQUIRED, verify)
        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertIn("does not match declared Test command", "\n".join(result.review_required))

    def test_fault_surviving_test_requires_review(self) -> None:
        verify = VERIFY_KILLED.replace("Mutated exit code: 1", "Mutated exit code: 0")
        result = SENSITIVITY.evaluate(SPEC_REQUIRED, verify)
        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertIn("fault survived", "\n".join(result.review_required))

    def test_unexpected_failure_does_not_count_as_killed(self) -> None:
        verify = VERIFY_KILLED.replace(
            "Expected failure observed: yes",
            "Expected failure observed: no",
        )
        result = SENSITIVITY.evaluate(SPEC_REQUIRED, verify)
        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertIn(
            "not for the expected protected behavior",
            "\n".join(result.review_required),
        )

    def test_restored_test_must_return_to_pass(self) -> None:
        verify = VERIFY_KILLED.replace("Restored exit code: 0", "Restored exit code: 1")
        result = SENSITIVITY.evaluate(SPEC_REQUIRED, verify)
        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertIn("did not return to PASS", "\n".join(result.review_required))

    def test_cli_json_and_exit_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spec = Path(tmp) / "SPEC.md"
            verify = Path(tmp) / "VERIFY.md"
            spec.write_text(SPEC_REQUIRED, encoding="utf-8")
            verify.write_text(
                VERIFY_KILLED.replace("Mutated exit code: 1", "Mutated exit code: 0"),
                encoding="utf-8",
            )
            process = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--spec",
                    str(spec),
                    "--verify",
                    str(verify),
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(process.returncode, 2)
        payload = json.loads(process.stdout)
        self.assertEqual(payload["status"], "REVIEW_REQUIRED")
        self.assertTrue(payload["active"])


if __name__ == "__main__":
    unittest.main()
