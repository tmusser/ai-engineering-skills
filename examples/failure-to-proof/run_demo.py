#!/usr/bin/env python3
"""Reproduce a passing-but-incomplete test suite and the missing-proof gate.

No API calls, hidden agent execution, third-party packages, or permanent writes.
Structured verification claims are generated from commands this runner executes.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
DEFAULT_FIXTURES = Path(__file__).resolve().parent
COVERAGE_CLI = REPO / "scripts" / "acceptance_coverage.py"
CONTRACT_PROBE = (
    "from export import export_csv; "
    "assert export_csv([], 'west') == 'order_id,region\\n', "
    "'zero matches must produce the header'"
)
TESTS = (
    ("AC-1", "test_export.ExportTests.test_matching_region_keeps_schema"),
    ("AC-2", "test_export.ExportTests.test_no_matches_keep_header"),
)


def invoke(arguments: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments, cwd=cwd, text=True, capture_output=True, check=False,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )


def suite(directory: Path) -> dict[str, int]:
    run = invoke([sys.executable, "-m", "unittest", "discover", "-p", "test_export.py"], directory)
    count = re.search(r"\bRan (\d+) tests?\b", run.stdout + run.stderr)
    return {"exit_code": run.returncode, "tests_run": int(count.group(1)) if count else 0}


def test_record(directory: Path, criterion: str, test_name: str, timestamp: str) -> dict[str, Any]:
    command = [sys.executable, "-m", "unittest", test_name]
    run = invoke(command, directory)
    return {
        "check": test_name.rsplit(".", 1)[-1],
        "command": shlex.join(command),
        "exit_code": run.returncode,
        "evidence_source": "command",
        "status": "PASS" if run.returncode == 0 else "FAIL",
        "evidence": f"Demo subprocess executed in {directory.name}/; exit={run.returncode}",
        "recorded_at": timestamp,
        "acceptance_criterion": criterion,
        "remaining_uncertainty": "Execution recorded by the demo; correctness not established by linkage alone.",
    }


def coverage(spec: Path, checks: list[dict[str, Any]], temporary: Path) -> dict[str, Any]:
    verify = temporary / "VERIFY.md"
    status = "PASS" if all(item["status"] == "PASS" for item in checks) else "FAIL"
    payload = json.dumps({"schema_version": 1, "checks": checks}, indent=2)
    fence = chr(96) * 3
    verify.write_text(
        f"# Verify\n\n## Verify gate\n\nStatus: {status}\n\n"
        f"## Structured verification evidence\n\n{fence}json\n{payload}\n{fence}\n",
        encoding="utf-8",
    )
    run = invoke([
        sys.executable, str(COVERAGE_CLI), "--spec", str(spec),
        "--verify", str(verify), "--format", "json",
    ], REPO)
    try:
        report = json.loads(run.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"coverage tool produced invalid JSON (exit={run.returncode}): {run.stderr.strip()}"
        ) from exc
    return {"exit_code": run.returncode, "status": report["status"], "rows": report["rows"],
            "warnings": report["warnings"]}


def demonstrate(fixtures: Path) -> dict[str, Any]:
    """Execute tests and independent behavior probes, then check evidence coverage."""
    spec = fixtures / "SPEC.md"
    before = fixtures / "before"
    after = fixtures / "after"
    if not spec.is_file() or not (before / "export.py").is_file() or not (after / "export.py").is_file():
        raise ValueError("fixture root must contain SPEC.md and before/after/export.py")
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    baseline_suite = suite(before)
    repaired_suite = suite(after)
    baseline_probe = invoke([sys.executable, "-c", CONTRACT_PROBE], before)
    repaired_probe = invoke([sys.executable, "-c", CONTRACT_PROBE], after)

    baseline_checks = [test_record(before, *TESTS[0], timestamp)]
    repaired_checks = [test_record(after, *target, timestamp) for target in TESTS]
    with tempfile.TemporaryDirectory(prefix="aes-proof-demo-") as directory:
        temporary = Path(directory)
        before_coverage = coverage(spec, baseline_checks, temporary)
        after_coverage = coverage(spec, repaired_checks, temporary)

    missing = {
        row["criterion"] for row in before_coverage["rows"] if row["status"] == "MISSING"
    }
    linked = {
        row["criterion"] for row in after_coverage["rows"] if row["status"] == "LINKED"
    }
    expected = (
        baseline_suite["exit_code"] == 0 and baseline_suite["tests_run"] == 1
        and repaired_suite["exit_code"] == 0 and repaired_suite["tests_run"] == 2
        and baseline_probe.returncode != 0 and repaired_probe.returncode == 0
        and all(record["status"] == "PASS" for record in baseline_checks + repaired_checks)
        and before_coverage["exit_code"] == 3
        and before_coverage["status"] == "REVIEW_REQUIRED"
        and missing == {"AC-2"}
        and after_coverage["exit_code"] == 0
        and after_coverage["status"] == "PASS"
        and linked == {"AC-1", "AC-2"}
    )
    return {
        "status": "PASS" if expected else "FAIL",
        "scenario": "CSV header omitted when filter returns no matches",
        "before": {
            "suite": baseline_suite,
            "contract_probe_exit_code": baseline_probe.returncode,
            "coverage": before_coverage,
        },
        "after": {
            "suite": repaired_suite,
            "contract_probe_exit_code": repaired_probe.returncode,
            "coverage": after_coverage,
        },
        "claim_boundary": (
            "The gate detects missing recorded AC-2 evidence, not the defect itself. "
            "The separately executed behavioral probe demonstrates the defect; "
            "coverage PASS means linkage, not comprehensive correctness."
        ),
        "benchmark_scope": "Fixed deterministic fixture; no coding agents or model pass rates measured.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--fixtures", type=Path, default=DEFAULT_FIXTURES,
                        help="Fixture root (default: this example folder)")
    args = parser.parse_args(argv)
    try:
        report = demonstrate(args.fixtures.resolve())
    except (OSError, ValueError, RuntimeError, KeyError, TypeError) as exc:
        if args.format == "json":
            print(json.dumps({"status": "ERROR", "error": str(exc)}))
        else:
            print(f"DEMO ERROR: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        before, after = report["before"], report["after"]
        print(f"FAILURE-TO-PROOF DEMO: {report['status']}")
        print(f"BEFORE: suite={before['suite']['exit_code']} ({before['suite']['tests_run']} test); "
              f"contract probe={before['contract_probe_exit_code']}; "
              f"coverage={before['coverage']['status']}")
        for row in before["coverage"]["rows"]:
            print(f"  {row['criterion']}: {row['status']}")
        print(f"AFTER: suite={after['suite']['exit_code']} ({after['suite']['tests_run']} tests); "
              f"contract probe={after['contract_probe_exit_code']}; "
              f"coverage={after['coverage']['status']}")
        for row in after["coverage"]["rows"]:
            print(f"  {row['criterion']}: {row['status']}")
        print("LIMITATION: " + report["claim_boundary"])
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
