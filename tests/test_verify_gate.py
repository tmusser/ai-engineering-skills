from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
SCRIPT = ROOT / "scripts" / "verify_gate.py"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text).lstrip("\n"), encoding="utf-8")


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


class VerifyGateTests(unittest.TestCase):
    maxDiff = None

    def make_repo(self, files: dict[str, str]) -> tuple[tempfile.TemporaryDirectory[str], Path, str]:
        tempdir = tempfile.TemporaryDirectory()
        repo = Path(tempdir.name)
        git(repo, "init")
        git(repo, "config", "user.name", "Test User")
        git(repo, "config", "user.email", "test@example.com")
        for relative_path, content in files.items():
            write_text(repo / relative_path, content)
        git(repo, "add", ".")
        git(repo, "commit", "-m", "base")
        base = git(repo, "rev-parse", "HEAD")
        self.addCleanup(tempdir.cleanup)
        return tempdir, repo, base

    def run_gate(self, repo: Path, base: str, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                PYTHON,
                str(SCRIPT),
                "--base",
                base,
                "--spec",
                "SPEC.md",
                "--verify",
                "VERIFY.md",
                *extra,
            ],
            cwd=repo,
            capture_output=True,
            text=True,
        )

    def assert_review_required(self, result: subprocess.CompletedProcess[str], expected_text: str) -> None:
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.startswith("VERIFY GATE: REVIEW_REQUIRED"))
        self.assertIn(expected_text, result.stdout)

    def test_clean_pass(self) -> None:
        _, repo, base = self.make_repo(
            {
                "SPEC.md": """
                    # Spec

                    ## Compatibility seams to preserve

                    - src/api.py

                    ## Invalid if

                    - output shape changes without updating VERIFY.md
                """,
                "VERIFY.md": """
                    # Verify

                    ## Verify gate

                    Status: PASS

                    ## Verify gate evidence

                    - Protected paths declared: src/api.py
                    - Forbidden paths declared: none
                """,
            }
        )

        result = self.run_gate(repo, base)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.startswith("VERIFY GATE: PASS"))

    def test_missing_spec_is_review_required(self) -> None:
        _, repo, base = self.make_repo(
            {
                "VERIFY.md": """
                    # Verify

                    ## Verify gate

                    Status: PASS
                """
            }
        )

        result = self.run_gate(repo, base)
        self.assert_review_required(result, "missing SPEC.md")

    def test_missing_compatibility_seams_is_review_required(self) -> None:
        _, repo, base = self.make_repo(
            {
                "SPEC.md": """
                    # Spec

                    ## Invalid if

                    - output shape changes without updating VERIFY.md
                """,
                "VERIFY.md": """
                    # Verify

                    ## Verify gate

                    Status: PASS
                """,
            }
        )

        result = self.run_gate(repo, base)
        self.assert_review_required(result, "compatibility seams")

    def test_missing_invalid_if_is_review_required(self) -> None:
        _, repo, base = self.make_repo(
            {
                "SPEC.md": """
                    # Spec

                    ## Compatibility seams to preserve

                    - src/api.py
                """,
                "VERIFY.md": """
                    # Verify

                    ## Verify gate

                    Status: PASS
                """,
            }
        )

        result = self.run_gate(repo, base)
        self.assert_review_required(result, "invalid-if constraints")

    def test_missing_verify_file_fails(self) -> None:
        _, repo, base = self.make_repo(
            {
                "SPEC.md": """
                    # Spec

                    ## Compatibility seams to preserve

                    - src/api.py

                    ## Invalid if

                    - output shape changes without updating VERIFY.md
                """
            }
        )

        result = self.run_gate(repo, base)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(result.stdout.startswith("VERIFY GATE: FAIL"))
        self.assertIn("missing VERIFY.md", result.stdout)

    def test_missing_verify_gate_section_fails(self) -> None:
        _, repo, base = self.make_repo(
            {
                "SPEC.md": """
                    # Spec

                    ## Compatibility seams to preserve

                    - src/api.py

                    ## Invalid if

                    - output shape changes without updating VERIFY.md
                """,
                "VERIFY.md": """
                    # Verify

                    Status: PASS
                """,
            }
        )

        result = self.run_gate(repo, base)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(result.stdout.startswith("VERIFY GATE: FAIL"))
        self.assertIn("missing verify gate section", result.stdout)

    def test_invalid_verify_status_fails(self) -> None:
        _, repo, base = self.make_repo(
            {
                "SPEC.md": """
                    # Spec

                    ## Compatibility seams to preserve

                    - src/api.py

                    ## Invalid if

                    - output shape changes without updating VERIFY.md
                """,
                "VERIFY.md": """
                    # Verify

                    ## Verify gate

                    Status: MAYBE
                """,
            }
        )

        result = self.run_gate(repo, base)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(result.stdout.startswith("VERIFY GATE: FAIL"))
        self.assertIn("missing valid verify gate status", result.stdout)

    def test_untracked_test_file_is_review_required(self) -> None:
        _, repo, base = self.make_repo(
            {
                "SPEC.md": """
                    # Spec

                    ## Compatibility seams to preserve

                    - src/api.py

                    ## Invalid if

                    - output shape changes without updating VERIFY.md
                """,
                "VERIFY.md": """
                    # Verify

                    ## Verify gate

                    Status: PASS
                """,
            }
        )
        write_text(
            repo / "tests" / "test_app.py",
            """
            import unittest


            class TestApp(unittest.TestCase):
                def test_app(self) -> None:
                    self.assertTrue(True)
            """,
        )

        result = self.run_gate(repo, base)
        self.assert_review_required(result, "tests changed")

    def test_staged_test_file_is_review_required(self) -> None:
        _, repo, base = self.make_repo(
            {
                "SPEC.md": """
                    # Spec

                    ## Compatibility seams to preserve

                    - src/api.py

                    ## Invalid if

                    - output shape changes without updating VERIFY.md
                """,
                "VERIFY.md": """
                    # Verify

                    ## Verify gate

                    Status: PASS
                """,
            }
        )
        write_text(
            repo / "tests" / "test_app.py",
            """
            import unittest


            class TestApp(unittest.TestCase):
                def test_app(self) -> None:
                    self.assertTrue(True)
            """,
        )
        git(repo, "add", "tests/test_app.py")

        result = self.run_gate(repo, base)
        self.assert_review_required(result, "tests changed")

    def test_deleted_test_file_is_review_required(self) -> None:
        _, repo, base = self.make_repo(
            {
                "SPEC.md": """
                    # Spec

                    ## Compatibility seams to preserve

                    - src/api.py

                    ## Invalid if

                    - output shape changes without updating VERIFY.md
                """,
                "VERIFY.md": """
                    # Verify

                    ## Verify gate

                    Status: PASS
                """,
                "tests/test_app.py": "print('base test')\n",
            }
        )
        (repo / "tests" / "test_app.py").unlink()

        result = self.run_gate(repo, base)
        self.assert_review_required(result, "tests changed")
        self.assertIn("- D tests/test_app.py", result.stdout)

    def test_deleted_dependency_file_is_review_required(self) -> None:
        _, repo, base = self.make_repo(
            {
                "SPEC.md": """
                    # Spec

                    ## Compatibility seams to preserve

                    - src/api.py

                    ## Invalid if

                    - output shape changes without updating VERIFY.md
                """,
                "VERIFY.md": """
                    # Verify

                    ## Verify gate

                    Status: PASS
                """,
                "requirements.txt": "pytest\n",
            }
        )
        (repo / "requirements.txt").unlink()

        result = self.run_gate(repo, base)
        self.assert_review_required(result, "dependencies changed")
        self.assertIn("- D requirements.txt", result.stdout)

    def test_forbidden_path_deleted_is_fail(self) -> None:
        _, repo, base = self.make_repo(
            {
                "SPEC.md": """
                    # Spec

                    ## Compatibility seams to preserve

                    - src/api.py

                    ## Invalid if

                    - output shape changes without updating VERIFY.md

                    ## Forbidden paths

                    - secrets/**
                """,
                "VERIFY.md": """
                    # Verify

                    ## Verify gate

                    Status: PASS
                """,
                "secrets/token.txt": "secret\n",
            }
        )
        (repo / "secrets" / "token.txt").unlink()

        result = self.run_gate(repo, base)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(result.stdout.startswith("VERIFY GATE: FAIL"))
        self.assertIn("forbidden path touched", result.stdout)

    def test_multiple_categories_accumulate_review_reasons(self) -> None:
        _, repo, base = self.make_repo(
            {
                "SPEC.md": """
                    # Spec

                    ## Compatibility seams to preserve

                    - src/api.py

                    ## Invalid if

                    - output shape changes without updating VERIFY.md
                """,
                "VERIFY.md": """
                    # Verify

                    ## Verify gate

                    Status: PASS
                """,
                "requirements.txt": "pytest\n",
            }
        )
        write_text(
            repo / "tests" / "test_app.py",
            """
            import unittest


            class TestApp(unittest.TestCase):
                def test_app(self) -> None:
                    self.assertTrue(True)
            """,
        )
        (repo / "requirements.txt").unlink()

        result = self.run_gate(repo, base)
        self.assert_review_required(result, "tests changed")
        self.assertIn("dependencies changed", result.stdout)
        self.assertIn("- A tests/test_app.py", result.stdout)
        self.assertIn("- D requirements.txt", result.stdout)

    def test_protected_path_touched_is_review_required(self) -> None:
        _, repo, base = self.make_repo(
            {
                "SPEC.md": """
                    # Spec

                    ## Compatibility seams to preserve

                    - src/api.py

                    ## Invalid if

                    - output shape changes without updating VERIFY.md

                    ## Protected paths

                    - src/api.py
                """,
                "VERIFY.md": """
                    # Verify

                    ## Verify gate

                    Status: PASS
                """,
                "src/api.py": "print('base')\n",
            }
        )
        write_text(repo / "src" / "api.py", "print('changed')\n")

        result = self.run_gate(repo, base)
        self.assert_review_required(result, "protected path touched")
        self.assertIn("- M src/api.py", result.stdout)

    def test_json_output_shape_includes_statuses(self) -> None:
        _, repo, base = self.make_repo(
            {
                "SPEC.md": """
                    # Spec

                    ## Compatibility seams to preserve

                    - src/api.py

                    ## Invalid if

                    - output shape changes without updating VERIFY.md
                """,
                "VERIFY.md": """
                    # Verify

                    ## Verify gate

                    Status: PASS
                """,
            }
        )
        write_text(repo / "tests" / "test_app.py", "print('test')\n")

        result = self.run_gate(repo, base, "--format", "json")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(
            set(payload),
            {
                "status",
                "checks",
                "failures",
                "review_required",
                "changed_files",
                "changed_file_statuses",
                "exit_code_policy",
            },
        )
        self.assertEqual(payload["status"], "REVIEW_REQUIRED")
        self.assertEqual(payload["changed_file_statuses"][0]["status"], "A")
        self.assertEqual(payload["changed_file_statuses"][0]["path"], "tests/test_app.py")

    def test_strict_review_exits_nonzero(self) -> None:
        _, repo, base = self.make_repo(
            {
                "SPEC.md": """
                    # Spec

                    ## Compatibility seams to preserve

                    - src/api.py

                    ## Invalid if

                    - output shape changes without updating VERIFY.md
                """,
                "VERIFY.md": """
                    # Verify

                    ## Verify gate

                    Status: PASS
                """,
            }
        )
        write_text(repo / "tests" / "test_app.py", "print('test')\n")

        result = self.run_gate(repo, base, "--strict-review")
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(result.stdout.startswith("VERIFY GATE: REVIEW_REQUIRED"))


if __name__ == "__main__":
    unittest.main()
