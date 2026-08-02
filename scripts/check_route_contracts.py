#!/usr/bin/env python3
"""Validate finite workflow-route contract scenarios.

This checker is intentionally not a runtime task router. It validates declared
scenarios against stable repository contracts: smallest adequate ceremony level,
risk coverage, conditional-skill triggers, and replacement routing behavior.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIOS = ROOT / "tests" / "fixtures" / "workflow_route_contracts.json"

VALID_SKILLS = {
    "analyze-mini",
    "build-one",
    "ceremony-budget",
    "checklist-mini",
    "constitution-lite",
    "grill-with-docs-lite",
    "handoff",
    "mini-spec",
    "scope-freeze",
    "ship-mini",
    "teach-back",
    "test-mini",
    "thin-plan",
    "verify-contract",
    "workspace-checkpoint",
}

MINIMUM_LEVEL_BY_RISK = {
    "behavior_change": 1,
    "scope_drift": 1,
    "compatibility_seam": 1,
    "ambiguity": 2,
    "continuation_risk": 0,
    "ownership_transfer": 0,
    "stale_analysis": 0,
    "test_integrity": 1,
    "activation_risk": 3,
    "autonomous_execution": 3,
    "consequential_decision": 0,
    "decision_impact": 3,
    "high_irreversibility": 3,
    "multi_slice": 3,
}

CONDITIONAL_SKILL_TRIGGERS = {
    "analyze-mini": {"stale_analysis"},
    "constitution-lite": {"autonomous_execution"},
    "handoff": {"continuation_risk"},
    "ship-mini": {"activation_risk", "autonomous_execution", "high_irreversibility"},
    "teach-back": {"ownership_transfer"},
    "test-mini": {"test_integrity"},
    "thin-plan": {"multi_slice"},
    "workspace-checkpoint": {"consequential_decision"},
}

LEVEL_REQUIREMENTS = {
    0: {"skills": set(), "guards": set()},
    1: {"skills": {"build-one"}, "guards": {"targeted-verification"}},
    2: {
        "skills": {"mini-spec", "build-one", "verify-contract"},
        "guards": {"targeted-verification"},
    },
    3: {
        "skills": {"mini-spec", "scope-freeze", "build-one", "verify-contract"},
        "guards": {"targeted-verification"},
    },
}


def _has_all(values: set[str], required: set[str]) -> bool:
    return required.issubset(values)


def _risk_is_covered(risk: str, skills: set[str], guards: set[str]) -> bool:
    coverage_checks = {
        "behavior_change": lambda: "build-one" in skills and "targeted-verification" in guards,
        "scope_drift": lambda: "scope-freeze" in skills or "inline-boundary" in guards,
        "compatibility_seam": lambda: "compatibility-regression-check" in guards,
        "ambiguity": lambda: "mini-spec" in skills,
        "continuation_risk": lambda: "handoff" in skills,
        "ownership_transfer": lambda: "teach-back" in skills,
        "stale_analysis": lambda: "analyze-mini" in skills,
        "test_integrity": lambda: "test-mini" in skills and "test-integrity-check" in guards,
        "activation_risk": lambda: "ship-mini" in skills and "rollback-plan" in guards,
        "autonomous_execution": lambda: "constitution-lite" in skills and "ship-mini" in skills,
        "consequential_decision": lambda: "workspace-checkpoint" in skills,
        "decision_impact": lambda: "verify-contract" in skills and "human-approval" in guards,
        "high_irreversibility": lambda: (
            "ship-mini" in skills
            and "human-approval" in guards
            and "rollback-plan" in guards
        ),
        "multi_slice": lambda: "thin-plan" in skills and "scope-freeze" in skills,
    }
    check = coverage_checks.get(risk)
    return bool(check and check())


def _require_string_list(
    scenario: dict[str, Any], field: str, scenario_id: str, errors: list[str]
) -> list[str]:
    value = scenario.get(field)
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        errors.append(f"{scenario_id}: {field} must be a list of strings")
        return []
    if len(value) != len(set(value)):
        errors.append(f"{scenario_id}: {field} contains duplicates")
    return value


def validate_scenarios(payload: dict[str, Any]) -> list[str]:
    """Return deterministic contract errors for a scenario payload."""
    errors: list[str] = []

    if payload.get("schema_version") != 1:
        errors.append("schema_version must be 1")

    scenarios = payload.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        errors.append("scenarios must be a non-empty list")
        return errors

    seen_ids: set[str] = set()

    for index, scenario in enumerate(scenarios):
        if not isinstance(scenario, dict):
            errors.append(f"scenario[{index}] must be an object")
            continue

        scenario_id = scenario.get("id")
        if not isinstance(scenario_id, str) or not scenario_id.strip():
            scenario_id = f"scenario[{index}]"
            errors.append(f"{scenario_id}: id must be a non-empty string")
        elif scenario_id in seen_ids:
            errors.append(f"{scenario_id}: duplicate id")
        else:
            seen_ids.add(scenario_id)

        summary = scenario.get("summary")
        if not isinstance(summary, str) or not summary.strip():
            errors.append(f"{scenario_id}: summary must be a non-empty string")

        level = scenario.get("expected_level")
        if not isinstance(level, int) or isinstance(level, bool) or level not in LEVEL_REQUIREMENTS:
            errors.append(f"{scenario_id}: expected_level must be an integer from 0 to 3")
            continue

        risks = set(_require_string_list(scenario, "risks", scenario_id, errors))
        skills = set(_require_string_list(scenario, "selected_skills", scenario_id, errors))
        guards = set(_require_string_list(scenario, "proof_guards", scenario_id, errors))
        forbidden = set(_require_string_list(scenario, "forbidden_skills", scenario_id, errors))

        unknown_risks = sorted(risks - MINIMUM_LEVEL_BY_RISK.keys())
        for risk in unknown_risks:
            errors.append(f"{scenario_id}: unknown risk {risk!r}")

        unknown_skills = sorted((skills | forbidden) - VALID_SKILLS)
        for skill in unknown_skills:
            errors.append(f"{scenario_id}: unknown skill {skill!r}")

        overlap = sorted(skills & forbidden)
        if overlap:
            errors.append(
                f"{scenario_id}: selected_skills and forbidden_skills overlap: {', '.join(overlap)}"
            )

        minimum_level = max((MINIMUM_LEVEL_BY_RISK.get(risk, 0) for risk in risks), default=0)
        if level != minimum_level:
            errors.append(
                f"{scenario_id}: expected_level {level} is not the smallest adequate level "
                f"{minimum_level} for its declared risks"
            )

        required = LEVEL_REQUIREMENTS[level]
        if level == 0 and skills:
            errors.append(f"{scenario_id}: Level 0 must not select workflow skills")
        elif not _has_all(skills, required["skills"]):
            missing = sorted(required["skills"] - skills)
            errors.append(f"{scenario_id}: level {level} missing required skills: {', '.join(missing)}")

        if not _has_all(guards, required["guards"]):
            missing = sorted(required["guards"] - guards)
            errors.append(f"{scenario_id}: level {level} missing required proof guards: {', '.join(missing)}")

        for skill, triggers in CONDITIONAL_SKILL_TRIGGERS.items():
            if skill in skills and risks.isdisjoint(triggers):
                errors.append(
                    f"{scenario_id}: conditional skill {skill!r} has no declared trigger "
                    f"({', '.join(sorted(triggers))})"
                )

        for risk in sorted(risks):
            if risk in MINIMUM_LEVEL_BY_RISK and not _risk_is_covered(risk, skills, guards):
                errors.append(f"{scenario_id}: risk {risk!r} is not covered by the declared route")

        route_explicit = scenario.get("route_explicit", False)
        if not isinstance(route_explicit, bool):
            errors.append(f"{scenario_id}: route_explicit must be a boolean")
        elif route_explicit:
            route_output = scenario.get("route_output")
            if route_output not in {"none", "delta"}:
                errors.append(
                    f"{scenario_id}: explicit routes must use route_output 'none' or 'delta'"
                )
            if scenario.get("routing_artifact", False):
                errors.append(f"{scenario_id}: explicit routes must not create a routing artifact")
            if "ceremony-budget" in skills:
                errors.append(
                    f"{scenario_id}: explicit routes must not append ceremony-budget as another stage"
                )

    return errors


def load_scenarios(path: Path) -> dict[str, Any]:
    """Load a UTF-8 JSON scenario file."""
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("top-level JSON value must be an object")
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=DEFAULT_SCENARIOS,
        help="scenario JSON path (default: tests/fixtures/workflow_route_contracts.json)",
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        payload = load_scenarios(args.path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors = [f"could not load {args.path}: {exc}"]
    else:
        errors = validate_scenarios(payload)

    result = {
        "status": "FAIL" if errors else "PASS",
        "scenario_count": len(payload.get("scenarios", [])) if "payload" in locals() else 0,
        "errors": errors,
    }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    elif errors:
        print("Workflow route contracts: FAIL")
        for error in errors:
            print(f"- {error}")
    else:
        print(f"Workflow route contracts: PASS ({result['scenario_count']} scenarios)")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
