#!/usr/bin/env python3
"""Read-only retry decision over an explicit, caller-maintained loop record."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


OUTCOMES = {"improved", "unchanged", "regressed", "error", "interrupted", "accepted"}


def evaluate(record: object) -> dict:
    """Fail closed on incomplete evidence; never execute or authorize a retry."""
    def result(status: str, decision: str, reason: str, attempted: int = 0) -> dict:
        return {"status": status, "decision": decision, "reason": reason,
                "attempted": attempted}

    def review(reason: str) -> dict:
        return result("REVIEW_REQUIRED", "STOP", reason)

    if not isinstance(record, dict):
        return review("Loop record must be an object.")
    if type(record.get("version")) is not int or record["version"] != 1:
        return review("Unsupported or missing version.")
    for key in ("loop_id", "artifact", "input_id", "evaluator_id", "feedback_signal",
                "acceptance_threshold", "revert_rule", "human_review_trigger"):
        if not isinstance(record.get(key), str) or not record[key].strip():
            return review(f"Missing non-empty {key}.")
    for key in ("max_attempts", "max_stalled"):
        if type(record.get(key)) is not int or record[key] < 1:
            return review(f"{key} must be a positive integer.")
    attempts = record.get("attempts")
    if not isinstance(attempts, list):
        return review("attempts must be the complete ordered ledger.")
    if type(record.get("review_required")) is not bool:
        return review("review_required must explicitly be true or false.")
    for number, attempt in enumerate(attempts, 1):
        if not isinstance(attempt, dict):
            return review(f"Attempt {number} must be an object.")
        if type(attempt.get("number")) is not int or attempt["number"] != number:
            return review("Attempt numbers must be contiguous, starting at 1.")
        if not isinstance(attempt.get("outcome"), str) or attempt["outcome"] not in OUTCOMES:
            return review(f"Attempt {number} has an unknown outcome.")
        for key in ("hypothesis", "evidence", "artifact_state"):
            if not isinstance(attempt.get(key), str) or not attempt[key].strip():
                return review(f"Attempt {number} is missing {key}.")
        if any(attempt.get(key) != record[key] for key in ("input_id", "evaluator_id")):
            return review(f"Attempt {number} uses stale inputs or a changed evaluator.")

    stalled = 0
    terminal = None
    for attempt in attempts:
        if terminal is not None:
            return result("FAIL", "STOP", "Ledger continues after a stop boundary.", len(attempts))
        outcome = attempt["outcome"]
        stalled = 0 if outcome in {"improved", "accepted"} else stalled + 1
        if outcome == "interrupted":
            terminal = ("REVIEW_REQUIRED", "STOP", "Reconcile the interrupted attempt before any retry.")
        elif outcome == "accepted":
            terminal = ("PASS", "VERIFY", "Acceptance reported; run the independent completion gate.")
        elif attempt["number"] >= record["max_attempts"]:
            terminal = ("FAIL", "STOP", "Attempt budget exhausted.")
        elif stalled >= record["max_stalled"]:
            terminal = ("FAIL", "STOP", "Consecutive no-progress limit reached.")
    if record["review_required"]:
        return result("REVIEW_REQUIRED", "STOP", "A human review trigger is unresolved.", len(attempts))
    if terminal:
        return result(*terminal, attempted=len(attempts))
    return result("PASS", "CONTINUE", "Recorded limits permit one more attempt; existing scope and permissions still apply.", len(attempts))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path, help="JSON loop contract and ordered attempt ledger")
    args = parser.parse_args(argv)
    try:
        record = json.loads(args.record.read_text(encoding="utf-8"))
        report = evaluate(record)
    except (OSError, UnicodeError, ValueError, RecursionError) as exc:
        report = {"status": "REVIEW_REQUIRED", "decision": "STOP",
                  "reason": f"Cannot read loop record: {exc}", "attempted": 0}
    print(json.dumps(report, indent=2))
    return {"PASS": 0, "FAIL": 1, "REVIEW_REQUIRED": 2}[report["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
