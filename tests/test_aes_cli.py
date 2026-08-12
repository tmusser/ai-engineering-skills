from __future__ import annotations

import contextlib
import importlib.util
import io
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "aes.py"
SPEC = importlib.util.spec_from_file_location("aes_cli", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
AES = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = AES
SPEC.loader.exec_module(AES)


class UnifiedCliTests(unittest.TestCase):
    def test_help_lists_stable_command_surface(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = AES.main(["--help"])
        self.assertEqual(status, 0)
        rendered = output.getvalue()
        for name in (
            "doctor",
            "spec",
            "scope",
            "lineage",
            "drift",
            "verify",
            "evidence",
            "summary",
            "context",
            "install",
        ):
            self.assertIn(name, rendered)
        self.assertIn("passed unchanged", rendered)

    def test_unknown_command_returns_usage_error_without_running_child(self) -> None:
        error = io.StringIO()
        with mock.patch.object(AES.subprocess, "call") as call, contextlib.redirect_stderr(error):
            status = AES.main(["invent-workflow"])
        self.assertEqual(status, 2)
        call.assert_not_called()
        self.assertIn("unknown command", error.getvalue())

    def test_python_commands_forward_arguments_unchanged(self) -> None:
        cases = {
            "doctor": ["--base", "origin/main", "--json"],
            "spec": ["--spec", "state/SPEC.md", "--format", "json"],
            "scope": ["--base", "HEAD~1", "--strict-review"],
            "lineage": ["--format", "json", "--verify", "state/VERIFY.md"],
            "drift": ["--target", "claude", "--only", "mini-spec"],
            "verify": ["--base", "main", "--format", "json"],
            "evidence": ["--base", "main", "--no-handoff"],
            "summary": ["--base", "main", "--no-handoff"],
            "context": ["fix", "export", "--budget", "500"],
        }
        for name, forwarded in cases.items():
            with self.subTest(name=name), mock.patch.object(
                AES.subprocess,
                "call",
                return_value=17,
            ) as call:
                status = AES.main([name, *forwarded])
            self.assertEqual(status, 17)
            command = AES.COMMANDS[name]
            call.assert_called_once_with(
                [sys.executable, str(command.target), *forwarded]
            )

    def test_subcommand_help_is_forwarded_instead_of_intercepted(self) -> None:
        with mock.patch.object(AES.subprocess, "call", return_value=0) as call:
            status = AES.main(["verify", "--help"])
        self.assertEqual(status, 0)
        call.assert_called_once_with(
            [sys.executable, str(AES.COMMANDS["verify"].target), "--help"]
        )

    def test_child_exit_code_is_preserved_exactly(self) -> None:
        with mock.patch.object(AES.subprocess, "call", return_value=3):
            self.assertEqual(AES.main(["context", "task", "--strict"]), 3)

    def test_install_delegates_to_existing_shell_wrapper_from_repo_root(self) -> None:
        with mock.patch.object(AES.shutil, "which", return_value="/bin/sh"), mock.patch.object(
            AES.subprocess,
            "call",
            return_value=0,
        ) as call:
            status = AES.main(["install", "--codex-user", "--only", "mini-spec"])
        self.assertEqual(status, 0)
        call.assert_called_once_with(
            [
                "/bin/sh",
                str(AES.COMMANDS["install"].target),
                "--codex-user",
                "--only",
                "mini-spec",
            ],
            cwd=AES.ROOT,
        )

    def test_install_reports_missing_shell_without_running_child(self) -> None:
        error = io.StringIO()
        with mock.patch.object(AES.shutil, "which", return_value=None), mock.patch.object(
            AES.subprocess,
            "call",
        ) as call, contextlib.redirect_stderr(error):
            status = AES.main(["install", "--help"])
        self.assertEqual(status, 127)
        call.assert_not_called()
        self.assertIn("'sh' is required", error.getvalue())

    def test_missing_target_is_infrastructure_error(self) -> None:
        missing = AES.Command("missing", "missing", ROOT / "not-there.py")
        error = io.StringIO()
        with mock.patch.object(AES.subprocess, "call") as call, contextlib.redirect_stderr(error):
            status = AES.run(missing, [])
        self.assertEqual(status, 127)
        call.assert_not_called()
        self.assertIn("target not found", error.getvalue())

    def test_os_error_is_mapped_to_command_not_found_style_exit(self) -> None:
        error = io.StringIO()
        with mock.patch.object(
            AES.subprocess,
            "call",
            side_effect=OSError("cannot execute"),
        ), contextlib.redirect_stderr(error):
            status = AES.main(["doctor"])
        self.assertEqual(status, 127)
        self.assertIn("unable to run doctor", error.getvalue())

    def test_dispatcher_does_not_add_a_working_directory_to_python_tools(self) -> None:
        with mock.patch.object(AES.subprocess, "call", return_value=0) as call:
            AES.main(["summary", "--base", "main"])
        _, kwargs = call.call_args
        self.assertNotIn("cwd", kwargs)


if __name__ == "__main__":
    unittest.main()
