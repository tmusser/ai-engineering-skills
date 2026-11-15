from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "examples" / "failure-to-proof" / "run_demo.py"
FIXTURES = RUNNER.parent


class FailureToProofShowcaseTests(unittest.TestCase):
    def run_demo(self, fixtures: Path = FIXTURES, *, fmt: str = "json"):
        return subprocess.run(
            [sys.executable, str(RUNNER), "--fixtures", str(fixtures), "--format", fmt],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )

    def copy_fixtures(self) -> Path:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        destination = Path(temp.name) / "demo"
        shutil.copytree(FIXTURES, destination)
        return destination

    def test_passing_suite_hides_real_regression_and_gate_flags_missing_evidence(self) -> None:
        process = self.run_demo()
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        result = json.loads(process.stdout)
        self.assertEqual(result["status"], "PASS")
        before, after = result["before"], result["after"]
        self.assertEqual(before["suite"], {"exit_code": 0, "tests_run": 1})
        self.assertEqual(after["suite"], {"exit_code": 0, "tests_run": 2})
        self.assertNotEqual(before["contract_probe_exit_code"], 0)
        self.assertEqual(after["contract_probe_exit_code"], 0)
        self.assertEqual(before["coverage"]["status"], "REVIEW_REQUIRED")
        self.assertEqual(before["coverage"]["exit_code"], 3)
        self.assertEqual(after["coverage"]["status"], "PASS")
        self.assertEqual(after["coverage"]["exit_code"], 0)
        self.assertEqual(
            [(row["criterion"], row["status"]) for row in before["coverage"]["rows"]],
            [("AC-1", "LINKED"), ("AC-2", "MISSING")],
        )
        self.assertEqual(
            [(row["criterion"], row["status"]) for row in after["coverage"]["rows"]],
            [("AC-1", "LINKED"), ("AC-2", "LINKED")],
        )
        self.assertIn("not the defect itself", result["claim_boundary"])
        self.assertIn("no coding agents", result["benchmark_scope"])

    def test_default_text_output_is_short_and_explains_limitations(self) -> None:
        process = self.run_demo(fmt="text")
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertIn("FAILURE-TO-PROOF DEMO: PASS", process.stdout)
        self.assertIn("BEFORE: suite=0 (1 test); contract probe=", process.stdout)
        self.assertIn("coverage=REVIEW_REQUIRED", process.stdout)
        self.assertIn("AFTER: suite=0 (2 tests); contract probe=0; coverage=PASS", process.stdout)
        self.assertIn("AC-2: MISSING", process.stdout)
        self.assertIn("LIMITATION:", process.stdout)

    def test_runner_does_not_modify_fixture_sources_or_create_bytecode(self) -> None:
        fixtures = self.copy_fixtures()
        source_files = [path for path in fixtures.rglob("*") if path.is_file()]
        before = {path.relative_to(fixtures): hashlib.sha256(path.read_bytes()).hexdigest()
                  for path in source_files}
        process = self.run_demo(fixtures)
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        after = {path.relative_to(fixtures): hashlib.sha256(path.read_bytes()).hexdigest()
                 for path in fixtures.rglob("*") if path.is_file()}
        self.assertEqual(before, after)

    def test_fixing_bug_in_before_makes_demo_fail_instead_of_claiming_success(self) -> None:
        fixtures = self.copy_fixtures()
        repaired = (fixtures / "after" / "export.py").read_text(encoding="utf-8")
        (fixtures / "before" / "export.py").write_text(repaired, encoding="utf-8")
        process = self.run_demo(fixtures)
        self.assertEqual(process.returncode, 1, process.stdout)
        result = json.loads(process.stdout)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["before"]["contract_probe_exit_code"], 0)

    def test_removing_regression_test_breaks_repaired_proof(self) -> None:
        fixtures = self.copy_fixtures()
        path = fixtures / "after" / "test_export.py"
        text = path.read_text(encoding="utf-8")
        self.assertIn("def test_no_matches_keep_header", text)
        path.write_text(text.replace(
            "def test_no_matches_keep_header", "def disabled_no_matches_keep_header"
        ), encoding="utf-8")
        process = self.run_demo(fixtures)
        self.assertEqual(process.returncode, 1, process.stdout)
        result = json.loads(process.stdout)
        self.assertEqual(result["status"], "FAIL")
        self.assertNotEqual(result["after"]["suite"]["tests_run"], 2)

    def test_removed_acceptance_criterion_breaks_demo_not_fake_success(self) -> None:
        fixtures = self.copy_fixtures()
        path = fixtures / "SPEC.md"
        text = path.read_text(encoding="utf-8")
        path.write_text(
            "\n".join(line for line in text.splitlines() if not line.startswith("- AC-2:")) + "\n",
            encoding="utf-8",
        )
        process = self.run_demo(fixtures)
        self.assertEqual(process.returncode, 1, process.stdout)
        self.assertEqual(json.loads(process.stdout)["status"], "FAIL")

    def test_missing_fixture_is_machine_readable_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            process = self.run_demo(Path(directory))
        self.assertEqual(process.returncode, 1)
        result = json.loads(process.stdout)
        self.assertEqual(result["status"], "ERROR")
        self.assertIn("fixture root", result["error"])


if __name__ == "__main__":
    unittest.main()
