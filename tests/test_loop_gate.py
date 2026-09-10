from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from loop_gate import evaluate


def record(*outcomes):
    data = {
        "version": 1, "loop_id": "export-1", "artifact": "export.py",
        "input_id": "fixture-sha", "evaluator_id": "test-sha",
        "feedback_signal": "original failing test + compatibility suite",
        "acceptance_threshold": "both pass", "max_attempts": 3, "max_stalled": 2,
        "revert_rule": "restore only this attempt's edits", "human_review_trigger": "scope change",
        "review_required": False, "attempts": [],
    }
    for n, outcome in enumerate(outcomes, 1):
        data["attempts"].append({"number": n, "outcome": outcome,
            "input_id": data["input_id"], "evaluator_id": data["evaluator_id"],
            "hypothesis": f"hypothesis {n}", "evidence": f"logs/{n}.txt",
            "artifact_state": f"snapshot-{n}"})
    return data


class LoopGateTests(unittest.TestCase):
    def test_documented_example_permits_one_more_attempt(self):
        data = json.loads((ROOT / "examples/bounded-loop.json").read_text())
        self.assertEqual(evaluate(data)["decision"], "CONTINUE")

    def test_new_loop_and_improving_attempt_can_continue(self):
        for data in (record(), record("improved"), record("error", "improved")):
            self.assertEqual(evaluate(data)["decision"], "CONTINUE")

    def test_stalled_loop_stops_before_total_budget(self):
        for outcomes in (("unchanged", "unchanged"), ("error", "regressed")):
            report = evaluate(record(*outcomes))
            self.assertEqual((report["status"], report["decision"]), ("FAIL", "STOP"))
            self.assertIn("no-progress", report["reason"])

    def test_improvement_does_not_reset_total_budget(self):
        self.assertEqual(evaluate(record("improved", "improved", "improved"))["status"], "FAIL")

    def test_acceptance_on_last_attempt_requires_verification(self):
        report = evaluate(record("improved", "improved", "accepted"))
        self.assertEqual((report["status"], report["decision"]), ("PASS", "VERIFY"))

    def test_interruption_never_grants_retry(self):
        self.assertEqual(evaluate(record("interrupted"))["status"], "REVIEW_REQUIRED")

    def test_continuing_after_any_terminal_boundary_fails(self):
        for outcomes in (("accepted", "improved"), ("interrupted", "improved"),
                         ("unchanged", "unchanged", "accepted"),
                         ("improved", "improved", "improved", "accepted")):
            self.assertEqual(evaluate(record(*outcomes))["status"], "FAIL")

    def test_resume_preserves_budget(self):
        data = json.loads(json.dumps(record("improved", "improved", "error")))
        self.assertEqual(evaluate(data)["status"], "FAIL")

    def test_changed_input_or_evaluator_invalidates_acceptance(self):
        for key in ("input_id", "evaluator_id"):
            data = record("accepted")
            data[key] = "new-revision"
            self.assertEqual(evaluate(data)["status"], "REVIEW_REQUIRED")

    def test_review_overrides_acceptance(self):
        data = record("accepted")
        data["review_required"] = True
        self.assertEqual(evaluate(data)["decision"], "STOP")

    def test_incomplete_and_malformed_records_fail_closed(self):
        for key in record():
            data = record()
            del data[key]
            self.assertEqual(evaluate(data)["status"], "REVIEW_REQUIRED", key)
        for value in (None, [], "", 0):
            self.assertEqual(evaluate(value)["status"], "REVIEW_REQUIRED")
        for key in ("max_attempts", "max_stalled"):
            for value in (True, 0, -1, 1.5, "3"):
                data = record()
                data[key] = value
                self.assertEqual(evaluate(data)["status"], "REVIEW_REQUIRED")
        for key, value in (("number", 2), ("number", True), ("outcome", []),
                           ("outcome", "pass"), ("evidence", ""), ("artifact_state", None)):
            data = record("improved")
            data["attempts"][0][key] = value
            self.assertEqual(evaluate(data)["status"], "REVIEW_REQUIRED")

    def test_evaluation_does_not_mutate_record(self):
        data = record("improved")
        before = copy.deepcopy(data)
        evaluate(data)
        self.assertEqual(data, before)

    def test_cli_exit_codes_and_dispatcher_from_other_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "loop.json"
            for data, code, decision in ((record(), 0, "CONTINUE"),
                                         (record("accepted"), 0, "VERIFY"),
                                         (record("error", "error"), 1, "STOP"),
                                         ({}, 2, "STOP")):
                path.write_text(json.dumps(data))
                before = path.read_bytes()
                run = subprocess.run([sys.executable, str(ROOT / "scripts/aes.py"),
                                      "loop", str(path)], cwd=tmp, capture_output=True, text=True)
                self.assertEqual(run.returncode, code, run.stderr)
                self.assertEqual(json.loads(run.stdout)["decision"], decision)
                self.assertEqual(path.read_bytes(), before)
            for raw in (b"not json", b"\xff"):
                path.write_bytes(raw)
                run = subprocess.run([sys.executable, str(ROOT / "scripts/loop_gate.py"), str(path)],
                                     capture_output=True, text=True)
                self.assertEqual(run.returncode, 2)
                self.assertEqual(json.loads(run.stdout)["decision"], "STOP")
            path.unlink()
            run = subprocess.run([sys.executable, str(ROOT / "scripts/loop_gate.py"), str(path)],
                                 capture_output=True, text=True)
            self.assertEqual(run.returncode, 2)


if __name__ == "__main__":
    unittest.main()
