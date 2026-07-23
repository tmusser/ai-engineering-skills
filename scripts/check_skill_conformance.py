#!/usr/bin/env python3
"""Check core skills against a small, versioned conformance profile."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT / "conformance" / "skill-contracts.json"


def load_profile(errors: list[str]) -> dict[str, Any]:
    """Load and minimally validate the conformance profile."""
    try:
        profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing profile: {PROFILE_PATH.relative_to(ROOT)}")
        return {}
    except json.JSONDecodeError as exc:
        errors.append(f"invalid profile JSON: {exc}")
        return {}

    if profile.get("profile_version") != 1:
        errors.append("profile_version must be 1")

    contracts = profile.get("contracts")
    if not isinstance(contracts, dict) or not contracts:
        errors.append("contracts must be a non-empty object")

    return profile


def check_contract(
    skill_name: str,
    contract: object,
    errors: list[str],
) -> None:
    """Check one skill file for the profile's required and forbidden signals."""
    if not skill_name or "/" in skill_name or "\\" in skill_name:
        errors.append(f"invalid skill name in profile: {skill_name!r}")
        return

    if not isinstance(contract, dict):
        errors.append(f"{skill_name}: contract must be an object")
        return

    required = contract.get("required_substrings", [])
    forbidden = contract.get("forbidden_substrings", [])

    if not isinstance(required, list) or not required:
        errors.append(f"{skill_name}: required_substrings must be a non-empty list")
        return
    if not all(isinstance(item, str) and item for item in required):
        errors.append(f"{skill_name}: required_substrings must contain non-empty strings")
        return
    if not isinstance(forbidden, list) or not all(
        isinstance(item, str) and item for item in forbidden
    ):
        errors.append(f"{skill_name}: forbidden_substrings must contain strings")
        return

    relative_path = Path("skills") / skill_name / "SKILL.md"
    skill_path = ROOT / relative_path
    if not skill_path.is_file():
        errors.append(f"{skill_name}: missing {relative_path.as_posix()}")
        return

    text = skill_path.read_text(encoding="utf-8")
    missing = [signal for signal in required if signal not in text]
    present_forbidden = [signal for signal in forbidden if signal in text]

    if missing:
        for signal in missing:
            errors.append(f"{skill_name}: missing required signal: {signal}")
    if present_forbidden:
        for signal in present_forbidden:
            errors.append(f"{skill_name}: contains forbidden signal: {signal}")

    if not missing and not present_forbidden:
        print(f"PASS {skill_name}: {len(required)} required signal(s)")


def main() -> int:
    """Run the versioned profile and return a CI-friendly exit code."""
    errors: list[str] = []
    profile = load_profile(errors)
    contracts = profile.get("contracts", {}) if profile else {}

    if isinstance(contracts, dict):
        for skill_name in sorted(contracts):
            check_contract(skill_name, contracts[skill_name], errors)

    if errors:
        print("Skill conformance: FAIL", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"Skill conformance: PASS ({len(contracts)} contract(s), profile v1)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
