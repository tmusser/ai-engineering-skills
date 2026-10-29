from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
SCRIPT = ROOT / "scripts" / "check_artifact_consistency.py"
SPEC = importlib.util.spec_from_file_location("artifact_consistency", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
LINTER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = LINTER
SPEC.loader.exec_module(LINTER)


SPEC_BASE = """# Spec

## Objective

Add a bounded export.

## Acceptance criteria

- Export returns canonical rows.

## Compatibility seams to preserve

- CLI output

## Compatibility probe gate

Compatibility probe requirement: NOT_APPLICABLE

## Implementation diff budget

Diff budget requirement: ENFORCED
- Max changed files: 3
- Max added lines: 120

## Invalid if

- output schema changes
"""

SCOPE = """SCOPE FREEZE
Task: bounded export
Allowed writes: src/**, tests/**
Read-only: schema.py
Forbidden: none
Review required if: tests changed
Max files changed: 2
Renames allowed: no
Deletions allowed: no
Allowed commands: python -m unittest
Stop when: export tests pass
Invalid if: output schema changes
"""

VERIFY = """# Verify

## Verify gate

Status: PASS

Scope gate: PASS
"""

HANDOFF = """# Handoff

## Continuation guardrails

- Verify gate status: PASS
- Review-required items: none
"""


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


class ArtifactConsistencyTests(unittest.TestCase):
    def make_repo(self, files: dict[str, str]) -> Path:
        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        root = Path(tempdir.name)
        git(root, "init", "-q")
        git(root, "config", "user.email", "test@example.com")
        git(root, "config", "user.name", "Test User")
        for name, text in files.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        git(root, "add", ".")
        git(root, "commit", "-qm", "initial")
        return root

    def check(self, result, name: str):
        return next(item for item in result.checks if item.name == name)

    def test_coherent_artifacts_pass(self) -> None:
        root = self.make_repo(
            {
                "SPEC.md": SPEC_BASE,
                "SCOPE.md": SCOPE,
                "VERIFY.md": VERIFY,
                "HANDOFF.md": HANDOFF,
            }
        )
        result = LINTER.evaluate(root)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(self.check(result, "spec-scope-budget").status, "PASS")
        self.assertEqual(self.check(result, "scope-verify").status, "PASS")
        self.assertEqual(self.check(result, "verify-handoff").status, "PASS")

    def test_scope_cap_above_spec_budget_requires_review(self) -> None:
        root = self.make_repo(
            {
                "SPEC.md": SPEC_BASE,
                "SCOPE.md": SCOPE.replace("Max files changed: 2", "Max files changed: 5"),
                "VERIFY.md": VERIFY,
            }
        )
        result = LINTER.evaluate(root)
        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertIn("5 > 3", "\n".join(result.review_required))

    def test_scope_and_verify_applicability_must_agree(self) -> None:
        root = self.make_repo(
            {
                "SPEC.md": SPEC_BASE,
                "SCOPE.md": SCOPE,
                "VERIFY.md": VERIFY.replace("Scope gate: PASS", "Scope gate: NOT_APPLICABLE"),
            }
        )
        result = LINTER.evaluate(root)
        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertIn(
            "marks Scope gate NOT_APPLICABLE",
            "\n".join(result.review_required),
        )

    def test_verify_cannot_claim_scope_result_without_scope_artifact(self) -> None:
        root = self.make_repo(
            {
                "SPEC.md": SPEC_BASE,
                "VERIFY.md": VERIFY,
            }
        )
        result = LINTER.evaluate(root)
        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertIn("SCOPE.md is absent", "\n".join(result.review_required))

    def test_verify_and_handoff_status_mismatch_requires_review(self) -> None:
        root = self.make_repo(
            {
                "SPEC.md": SPEC_BASE,
                "VERIFY.md": VERIFY.replace("Scope gate: PASS\n", ""),
                "HANDOFF.md": HANDOFF.replace("Verify gate status: PASS", "Verify gate status: FAIL"),
            }
        )
        result = LINTER.evaluate(root)
        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertIn("HANDOFF=FAIL, VERIFY=PASS", "\n".join(result.review_required))

    def test_handoff_review_items_must_match_verify_posture(self) -> None:
        root = self.make_repo(
            {
                "SPEC.md": SPEC_BASE,
                "VERIFY.md": VERIFY.replace("Scope gate: PASS\n", ""),
                "HANDOFF.md": HANDOFF.replace(
                    "Review-required items: none",
                    "Review-required items: inspect export fallback",
                ),
            }
        )
        result = LINTER.evaluate(root)
        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertIn(
            "carries review-required items while VERIFY.md is PASS",
            "\n".join(result.review_required),
        )

    def test_active_contract_mismatch_is_fail(self) -> None:
        root = self.make_repo(
            {
                "SPEC.md": (
                    "Contract ID: task-2 | Parent: none | Base commit: HEAD\n"
                    "Replan reason: none\n" + SPEC_BASE
                ),
                "VERIFY.md": "Contract ID: task-other\n" + VERIFY.replace("Scope gate: PASS\n", ""),
            }
        )
        result = LINTER.evaluate(root)
        self.assertEqual(result.status, "FAIL")
        self.assertIn("does not match active contract", "\n".join(result.failures))

    def test_acceptance_coverage_is_composed_when_spec_opts_in(self) -> None:
        spec = SPEC_BASE.replace(
            "- Export returns canonical rows.",
            "- AC-1: Export returns canonical rows.",
        )
        root = self.make_repo(
            {
                "SPEC.md": spec,
                "VERIFY.md": VERIFY.replace("Scope gate: PASS\n", ""),
            }
        )
        result = LINTER.evaluate(root)
        self.assertEqual(result.status, "REVIEW_REQUIRED")
        coverage = self.check(result, "acceptance-coverage")
        self.assertEqual(coverage.status, "REVIEW_REQUIRED")
        self.assertIn("AC-1: MISSING", "\n".join(coverage.details))

    def test_required_compatibility_evidence_is_composed(self) -> None:
        spec = SPEC_BASE.replace(
            "Compatibility probe requirement: NOT_APPLICABLE",
            """Compatibility probe requirement: REQUIRED

- Probe ID: cli-json
  - Seam: CLI JSON output
  - Baseline command: python -m app --format json
  - Baseline result: PASS
  - Baseline evidence: baseline passed
  - Expected invariant: keys stay stable""",
        )
        root = self.make_repo(
            {
                "SPEC.md": spec,
                "VERIFY.md": VERIFY.replace("Scope gate: PASS\n", ""),
            }
        )
        result = LINTER.evaluate(root)
        self.assertEqual(result.status, "REVIEW_REQUIRED")
        compatibility = self.check(result, "compatibility-evidence")
        self.assertEqual(compatibility.status, "REVIEW_REQUIRED")
        self.assertIn("missing post-change evidence", compatibility.details[0])

    def test_legacy_artifacts_without_optional_contracts_stay_compatible(self) -> None:
        root = self.make_repo(
            {
                "SPEC.md": """# Spec

## Objective

Small change.

## Acceptance criteria

- Existing output stays stable.

## Compatibility seams to preserve

- output

## Invalid if

- output changes
""",
                "VERIFY.md": """# Verify

## Verify gate

Status: PASS
""",
            }
        )
        result = LINTER.evaluate(root)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(self.check(result, "acceptance-coverage").status, "NOT_APPLICABLE")
        self.assertEqual(self.check(result, "compatibility-evidence").status, "NOT_APPLICABLE")

    def test_cli_json_and_exit_code_are_stable(self) -> None:
        root = self.make_repo(
            {
                "SPEC.md": SPEC_BASE,
                "SCOPE.md": SCOPE.replace("Max files changed: 2", "Max files changed: 5"),
                "VERIFY.md": VERIFY,
            }
        )
        result = subprocess.run(
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
        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "REVIEW_REQUIRED")
        self.assertEqual(
            next(check for check in payload["checks"] if check["name"] == "spec-scope-budget")["status"],
            "REVIEW_REQUIRED",
        )


if __name__ == "__main__":
    unittest.main()
