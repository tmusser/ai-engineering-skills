from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "change_proof.py"
SPEC = importlib.util.spec_from_file_location("change_proof", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
PROOF = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PROOF
SPEC.loader.exec_module(PROOF)


SPEC_REQUIRED = """# Spec

## Change proof gate

Change proof requirement: REQUIRED

- Change ID: export-empty
  - Baseline commit: abcdef1234567890
  - Baseline command: python -m pytest tests/test_export.py -k empty
  - Baseline exit code: 1
  - Baseline evidence: assertion fails because empty export contains a body row
  - Expected delta: targeted empty-export test changes from failing to passing
"""

VERIFY_PASS = """# Verify

## Change proof evidence

- Change ID: export-empty
  - Proof command: python -m pytest tests/test_export.py -k empty
  - Proof exit code: 0
  - Delta result: PASS
  - Proof evidence: targeted empty-export assertion passes
"""


class ChangeProofTests(unittest.TestCase):
    def test_legacy_spec_is_not_applicable(self) -> None:
        result = PROOF.evaluate("# Spec\n", "# Verify\n")
        self.assertFalse(result.active)
        self.assertEqual(result.status, "NOT_APPLICABLE")

    def test_explicit_not_applicable_is_compatible(self) -> None:
        spec = """# Spec

## Change proof gate

Change proof requirement: NOT_APPLICABLE
"""
        result = PROOF.evaluate(spec, None)
        self.assertEqual(result.status, "NOT_APPLICABLE")

    def test_required_baseline_to_proof_passes(self) -> None:
        result = PROOF.evaluate(
            SPEC_REQUIRED,
            VERIFY_PASS,
            expected_base_commit="abcdef1234567890",
        )
        self.assertEqual(result.status, "PASS")
        self.assertEqual(result.records[0].baseline_exit_code, 1)
        self.assertEqual(result.records[0].proof_exit_code, 0)

    def test_optional_template_heading_is_supported(self) -> None:
        spec = SPEC_REQUIRED.replace(
            "## Change proof gate",
            "## Change proof gate (optional)",
        )
        result = PROOF.evaluate(spec, VERIFY_PASS)
        self.assertEqual(result.status, "PASS")

    def test_baseline_must_match_verification_base(self) -> None:
        result = PROOF.evaluate(
            SPEC_REQUIRED,
            VERIFY_PASS,
            expected_base_commit="9999999999999999",
        )
        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertIn("does not match verification base", "\n".join(result.review_required))

    def test_short_sha_can_match_full_base(self) -> None:
        spec = SPEC_REQUIRED.replace("abcdef1234567890", "abcdef1")
        result = PROOF.evaluate(
            spec,
            VERIFY_PASS,
            expected_base_commit="abcdef1234567890",
        )
        self.assertEqual(result.status, "PASS")

    def test_missing_proof_requires_review(self) -> None:
        result = PROOF.evaluate(SPEC_REQUIRED, "# Verify\n")
        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertIn("missing change-proof evidence", "\n".join(result.review_required))

    def test_proof_command_must_match_baseline_command(self) -> None:
        verify = VERIFY_PASS.replace(
            "python -m pytest tests/test_export.py -k empty",
            "python -m pytest tests/test_export.py",
        )
        result = PROOF.evaluate(SPEC_REQUIRED, verify)
        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertIn("does not match baseline command", "\n".join(result.review_required))

    def test_explicit_failed_delta_is_fail(self) -> None:
        verify = VERIFY_PASS.replace("Delta result: PASS", "Delta result: FAIL")
        result = PROOF.evaluate(SPEC_REQUIRED, verify)
        self.assertEqual(result.status, "FAIL")
        self.assertIn("expected delta was not proven", result.failures[0])

    def test_pass_with_nonzero_proof_exit_requires_review(self) -> None:
        verify = VERIFY_PASS.replace("Proof exit code: 0", "Proof exit code: 2")
        result = PROOF.evaluate(SPEC_REQUIRED, verify)
        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertIn("claims PASS but proof command exited 2", "\n".join(result.review_required))

    def test_undeclared_change_id_requires_review(self) -> None:
        verify = VERIFY_PASS + """
- Change ID: surprise
  - Proof command: pytest x
  - Proof exit code: 0
  - Delta result: PASS
  - Proof evidence: surprise
"""
        result = PROOF.evaluate(SPEC_REQUIRED, verify)
        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertIn("undeclared Change ID", "\n".join(result.review_required))

    def test_cli_json_and_exit_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "SPEC.md").write_text(SPEC_REQUIRED, encoding="utf-8")
            (root / "VERIFY.md").write_text(
                VERIFY_PASS.replace("Delta result: PASS", "Delta result: FAIL"),
                encoding="utf-8",
            )
            process = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--root",
                    str(root),
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(process.returncode, 1)
        payload = json.loads(process.stdout)
        self.assertEqual(payload["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
