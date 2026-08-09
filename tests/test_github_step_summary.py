from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "render_github_step_summary.py"
SPEC = importlib.util.spec_from_file_location("github_step_summary", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
SUMMARY = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = SUMMARY
SPEC.loader.exec_module(SUMMARY)


class GitHubStepSummaryTests(unittest.TestCase):
    def child(
        self,
        name: str,
        returncode: int,
        stdout: str,
        stderr: str = "",
    ):
        return SUMMARY.ChildResult(name, returncode, stdout, stderr)

    def test_requires_step_summary_target_before_running_children(self) -> None:
        error = io.StringIO()
        with mock.patch.object(SUMMARY, "run_child") as run_child, contextlib.redirect_stderr(error):
            status = SUMMARY.main([], env={})
        self.assertEqual(status, 2)
        run_child.assert_not_called()
        self.assertIn("GITHUB_STEP_SUMMARY is not set", error.getvalue())

    def test_reporting_mode_publishes_non_green_evidence_without_failing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary_path = Path(tmp) / "step-summary.md"
            doctor = self.child(
                "workflow doctor",
                2,
                "WORKFLOW DOCTOR: REVIEW_REQUIRED\nNEXT MOVE: resolve review",
            )
            evidence = self.child(
                "PR evidence renderer",
                1,
                "## PR Evidence Summary\n\n- Overall: **REVIEW_REQUIRED**\n",
            )
            with mock.patch.object(SUMMARY, "run_child", side_effect=[doctor, evidence]):
                status = SUMMARY.main(
                    ["--base", "origin/main"],
                    env={"GITHUB_STEP_SUMMARY": str(summary_path)},
                )

            self.assertEqual(status, 0)
            rendered = summary_path.read_text(encoding="utf-8")
            self.assertIn("WORKFLOW DOCTOR: REVIEW_REQUIRED", rendered)
            self.assertIn("## PR Evidence Summary", rendered)
            self.assertIn("Reporting only", rendered)

    def test_forwards_artifact_paths_and_base_to_both_tools(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary_path = Path(tmp) / "summary.md"
            calls = []

            def fake_run(name, argv, cwd):
                calls.append((name, argv, cwd))
                output = (
                    "WORKFLOW DOCTOR: PASS"
                    if name == "workflow doctor"
                    else "## PR Evidence Summary\n\n- Overall: **PASS**\n"
                )
                return self.child(name, 0, output)

            with mock.patch.object(SUMMARY, "run_child", side_effect=fake_run):
                status = SUMMARY.main(
                    [
                        "--root",
                        tmp,
                        "--base",
                        "abc123",
                        "--spec",
                        "state/SPEC.md",
                        "--scope",
                        "state/SCOPE.md",
                        "--verify",
                        "state/VERIFY.md",
                        "--handoff",
                        "state/HANDOFF.md",
                        "--summary",
                        str(summary_path),
                    ],
                    env={},
                )

            self.assertEqual(status, 0)
            self.assertEqual(len(calls), 2)
            doctor_argv = calls[0][1]
            evidence_argv = calls[1][1]
            self.assertIn("abc123", doctor_argv)
            self.assertIn("abc123", evidence_argv)
            for path in ("state/SPEC.md", "state/VERIFY.md", "state/HANDOFF.md"):
                self.assertIn(path, doctor_argv)
                self.assertIn(path, evidence_argv)
            self.assertIn("state/SCOPE.md", doctor_argv)
            self.assertNotIn("state/SCOPE.md", evidence_argv)
            self.assertEqual(calls[0][2], Path(tmp).resolve())
            self.assertEqual(calls[1][2], Path(tmp).resolve())

    def test_no_handoff_only_omits_continuation_from_evidence_renderer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary_path = Path(tmp) / "summary.md"
            calls = []

            def fake_run(name, argv, cwd):
                calls.append((name, argv))
                output = (
                    "WORKFLOW DOCTOR: PASS"
                    if name == "workflow doctor"
                    else "## PR Evidence Summary\n"
                )
                return self.child(name, 0, output)

            with mock.patch.object(SUMMARY, "run_child", side_effect=fake_run):
                status = SUMMARY.main(
                    ["--no-handoff", "--summary", str(summary_path)],
                    env={},
                )

            self.assertEqual(status, 0)
            self.assertIn("--handoff", calls[0][1])
            self.assertIn("--no-handoff", calls[1][1])
            self.assertNotIn("--handoff", calls[1][1])

    def test_runs_evidence_renderer_even_when_doctor_is_non_green(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary_path = Path(tmp) / "summary.md"
            with mock.patch.object(
                SUMMARY,
                "run_child",
                side_effect=[
                    self.child("workflow doctor", 1, "WORKFLOW DOCTOR: FAIL"),
                    self.child("PR evidence renderer", 1, "## PR Evidence Summary\n"),
                ],
            ) as run_child:
                status = SUMMARY.main(["--summary", str(summary_path)], env={})

            self.assertEqual(status, 0)
            self.assertEqual(run_child.call_count, 2)

    def test_launch_failure_is_reported_after_publishing_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary_path = Path(tmp) / "summary.md"
            error = io.StringIO()
            with mock.patch.object(
                SUMMARY,
                "run_child",
                side_effect=[
                    self.child("workflow doctor", 127, "", "unable to run doctor"),
                    self.child("PR evidence renderer", 0, "## PR Evidence Summary\n"),
                ],
            ), contextlib.redirect_stderr(error):
                status = SUMMARY.main(["--summary", str(summary_path)], env={})

            self.assertEqual(status, 2)
            rendered = summary_path.read_text(encoding="utf-8")
            self.assertIn("Adapter diagnostics", rendered)
            self.assertIn("could not be launched", rendered)
            self.assertIn("published with adapter diagnostics", error.getvalue())

    def test_appends_without_overwriting_existing_step_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary_path = Path(tmp) / "summary.md"
            summary_path.write_text("existing summary\n", encoding="utf-8")
            with mock.patch.object(
                SUMMARY,
                "run_child",
                side_effect=[
                    self.child("workflow doctor", 0, "WORKFLOW DOCTOR: PASS"),
                    self.child("PR evidence renderer", 0, "## PR Evidence Summary\n"),
                ],
            ):
                status = SUMMARY.main(["--summary", str(summary_path)], env={})

            self.assertEqual(status, 0)
            rendered = summary_path.read_text(encoding="utf-8")
            self.assertTrue(rendered.startswith("existing summary\n"))
            self.assertIn("AI Engineering Skills", rendered)


if __name__ == "__main__":
    unittest.main()
