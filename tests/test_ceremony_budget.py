from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = (ROOT / "skills" / "ceremony-budget" / "SKILL.md").read_text(encoding="utf-8")
DOC = (ROOT / "docs" / "ceremony-budget.md").read_text(encoding="utf-8")
SKILL_COMPACT = " ".join(SKILL.split())
DOC_COMPACT = " ".join(DOC.split())


class CeremonyBudgetContractTests(unittest.TestCase):
    def test_routes_replace_explicit_workflows_instead_of_appending(self) -> None:
        self.assertIn("replaces the default larger workflow", SKILL_COMPACT)
        self.assertIn("Do not regenerate the full route", SKILL_COMPACT)
        self.assertIn("Route already explicit; no additional ceremony block needed.", SKILL_COMPACT)
        self.assertIn("do not append a second process contract", SKILL_COMPACT)
        self.assertIn("Do not create `CEREMONY_BUDGET.md`", SKILL)
        self.assertIn("invoke several skills merely because they are available", SKILL)

    def test_output_contract_has_concrete_next_action_and_no_ledger(self) -> None:
        self.assertIn("Next action: ...", SKILL_COMPACT)
        self.assertIn("Proof and stop: ...", SKILL_COMPACT)
        self.assertIn("budget ledger by default", SKILL_COMPACT)
        self.assertIn("run commands solely to document route selection", SKILL_COMPACT)

    def test_light_routes_start_immediately_and_handoff_is_conditional(self) -> None:
        self.assertIn("inline boundary -> build-one -> targeted verify -> stop", SKILL_COMPACT)
        self.assertIn("compact mini-spec -> build-one -> targeted test -> verify-contract -> stop", SKILL_COMPACT)
        self.assertIn("Implementation must follow immediately", SKILL_COMPACT)
        self.assertIn("Use `handoff` only when", SKILL_COMPACT)
        self.assertNotIn("Level 1: `scope-freeze", DOC)

    def test_light_routes_preserve_named_compatibility_seams(self) -> None:
        self.assertIn(
            "For each named preserved behavior, non-goal, or adjacent compatibility seam",
            SKILL_COMPACT,
        )
        self.assertIn(
            "reserve the cheapest relevant negative or regression check",
            SKILL_COMPACT,
        )
        self.assertIn(
            "must not omit a cheap check that protects an explicitly preserved behavior",
            SKILL_COMPACT,
        )
        self.assertIn("does not by itself require a larger route", SKILL_COMPACT)

    def test_stop_and_failure_discipline_protects_proof_without_reassurance_loops(self) -> None:
        self.assertIn("required verification has passed", SKILL_COMPACT)
        self.assertIn("do not rerun an already passing proof validator without a concrete reason", SKILL_COMPACT)
        self.assertIn("repeat Git or status commands for reassurance", SKILL_COMPACT)
        self.assertIn("inspect the first actionable traceback or mismatch", SKILL_COMPACT)
        self.assertIn("rerun the narrow check", SKILL_COMPACT)

    def test_documentation_labels_task_7_as_suggestive_additive_protocol_evidence(self) -> None:
        self.assertIn("Observed tradeoff", DOC)
        self.assertIn("One controlled Task 7 Codex pair", DOC_COMPACT)
        self.assertIn("additive ceremony protocol", DOC_COMPACT)
        self.assertIn("suggestive only", DOC_COMPACT)
        self.assertIn("does not isolate the base skill", DOC_COMPACT)
        self.assertIn("benchmark-informed hypothesis awaiting another controlled pair", DOC_COMPACT)


if __name__ == "__main__":
    unittest.main()
