from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "scripts" / "check_route_contracts.py"
CASES_PATH = ROOT / "tests" / "fixtures" / "conditional_activation_regressions.json"
ROUTES_PATH = ROOT / "tests" / "fixtures" / "workflow_route_contracts.json"

SPEC = importlib.util.spec_from_file_location("check_route_contracts", CHECKER_PATH)
assert SPEC is not None and SPEC.loader is not None
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)

EXPECTED_CASE_IDS = {
    "missing-analysis-is-not-stale-analysis",
    "long-chat-is-not-a-workspace-checkpoint",
    "ordinary-release-is-not-activation-risk",
    "clean-completion-is-not-continuation-risk",
    "installed-skills-are-not-auto-invoked",
    "verification-pass-is-not-ownership-transfer",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def cases() -> list[dict[str, Any]]:
    payload = load_json(CASES_PATH)
    assert payload.get("schema_version") == 1
    value = payload.get("cases")
    assert isinstance(value, list)
    return value


def route_payload(case: dict[str, Any]) -> dict[str, Any]:
    route = copy.deepcopy(case["route"])
    route["id"] = case["id"]
    route["summary"] = case["summary"]
    return {"schema_version": 1, "scenarios": [route]}


def route_index() -> dict[str, dict[str, Any]]:
    payload = load_json(ROUTES_PATH)
    value = payload.get("scenarios")
    assert isinstance(value, list)
    return {item["id"]: item for item in value}


class ConditionalActivationRegressionTests(unittest.TestCase):
    def test_suite_covers_the_six_named_false_signals(self) -> None:
        actual_ids = {case["id"] for case in cases()}
        self.assertEqual(actual_ids, EXPECTED_CASE_IDS)

    def test_false_signal_routes_are_valid_and_source_backed(self) -> None:
        for case in cases():
            with self.subTest(case=case["id"]):
                errors = CHECKER.validate_scenarios(route_payload(case))
                self.assertEqual(errors, [])

                source = ROOT / case["contract_source"]
                self.assertTrue(source.is_file(), source)
                text = source.read_text(encoding="utf-8")
                for phrase in case["required_phrases"]:
                    self.assertIn(phrase, text)

    def test_false_signals_do_not_activate_conditional_skills(self) -> None:
        for case in cases():
            for skill in case["guarded_skills"]:
                with self.subTest(case=case["id"], skill=skill):
                    payload = route_payload(case)
                    route = payload["scenarios"][0]
                    route["selected_skills"].append(skill)
                    route["forbidden_skills"].remove(skill)

                    errors = CHECKER.validate_scenarios(payload)
                    expected = f"conditional skill {skill!r} has no declared trigger"
                    self.assertTrue(
                        any(expected in error for error in errors),
                        f"expected {expected!r}; got {errors!r}",
                    )

    def test_positive_controls_prove_skills_are_conditional_not_banned(self) -> None:
        routes = route_index()
        all_routes = load_json(ROUTES_PATH)
        self.assertEqual(CHECKER.validate_scenarios(all_routes), [])

        for case in cases():
            for skill, control_id in case["positive_controls"].items():
                with self.subTest(case=case["id"], skill=skill, control=control_id):
                    control = routes[control_id]
                    self.assertIn(skill, control["selected_skills"])
                    triggers = CHECKER.CONDITIONAL_SKILL_TRIGGERS[skill]
                    self.assertFalse(set(control["risks"]).isdisjoint(triggers))

    def test_installed_skill_case_covers_every_conditional_skill(self) -> None:
        installed_case = next(
            case for case in cases() if case["false_signal"] == "skills_installed"
        )
        expected = set(CHECKER.CONDITIONAL_SKILL_TRIGGERS)
        self.assertEqual(set(installed_case["guarded_skills"]), expected)
        self.assertEqual(set(installed_case["forbidden_skills"]), expected)
        self.assertEqual(set(installed_case["positive_controls"]), expected)

    def test_false_signal_labels_are_unique(self) -> None:
        labels = [case["false_signal"] for case in cases()]
        self.assertEqual(len(labels), len(set(labels)))


if __name__ == "__main__":
    unittest.main()
