from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_route_contracts.py"
FIXTURES = ROOT / "tests" / "fixtures" / "workflow_route_contracts.json"

SPEC = importlib.util.spec_from_file_location("check_route_contracts", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


def load_payload() -> dict[str, object]:
    return json.loads(FIXTURES.read_text(encoding="utf-8"))


def scenario(payload: dict[str, object], scenario_id: str) -> dict[str, object]:
    scenarios = payload["scenarios"]
    assert isinstance(scenarios, list)
    for item in scenarios:
        assert isinstance(item, dict)
        if item.get("id") == scenario_id:
            return item
    raise AssertionError(f"missing scenario {scenario_id}")


class WorkflowRouteContractTests(unittest.TestCase):
    def test_golden_scenarios_pass(self) -> None:
        self.assertEqual(CHECKER.validate_scenarios(load_payload()), [])

    def test_checker_rejects_heavier_than_required_route(self) -> None:
        payload = copy.deepcopy(load_payload())
        item = scenario(payload, "tiny-doc-typo")
        item["expected_level"] = 2
        item["selected_skills"] = ["mini-spec", "build-one", "verify-contract"]
        item["proof_guards"] = ["targeted-verification"]

        errors = CHECKER.validate_scenarios(payload)

        self.assertTrue(any("not the smallest adequate level" in error for error in errors))

    def test_checker_rejects_conditional_skill_without_trigger(self) -> None:
        payload = copy.deepcopy(load_payload())
        item = scenario(payload, "ambiguous-export-slice")
        selected = item["selected_skills"]
        assert isinstance(selected, list)
        selected.append("ship-mini")

        errors = CHECKER.validate_scenarios(payload)

        self.assertTrue(any("conditional skill 'ship-mini' has no declared trigger" in error for error in errors))

    def test_checker_rejects_uncovered_compatibility_seam(self) -> None:
        payload = copy.deepcopy(load_payload())
        item = scenario(payload, "bounded-parser-compatibility")
        guards = item["proof_guards"]
        assert isinstance(guards, list)
        guards.remove("compatibility-regression-check")

        errors = CHECKER.validate_scenarios(payload)

        self.assertTrue(any("risk 'compatibility_seam' is not covered" in error for error in errors))

    def test_checker_rejects_second_route_for_explicit_wrapper(self) -> None:
        payload = copy.deepcopy(load_payload())
        item = scenario(payload, "explicit-wrapper-no-second-route")
        item["route_output"] = "full"
        item["routing_artifact"] = True
        selected = item["selected_skills"]
        assert isinstance(selected, list)
        selected.append("ceremony-budget")
        forbidden = item["forbidden_skills"]
        assert isinstance(forbidden, list)
        forbidden.remove("ceremony-budget")

        errors = CHECKER.validate_scenarios(payload)

        self.assertTrue(any("route_output 'none' or 'delta'" in error for error in errors))
        self.assertTrue(any("must not create a routing artifact" in error for error in errors))
        self.assertTrue(any("must not append ceremony-budget" in error for error in errors))

    def test_cli_reports_pass(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(FIXTURES)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Workflow route contracts: PASS (12 scenarios)", result.stdout)


if __name__ == "__main__":
    unittest.main()
