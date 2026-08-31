from __future__ import annotations

import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
PACK_SCRIPT = ROOT / "scripts" / "context_pack.py"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text).lstrip("\n"), encoding="utf-8")


def route_file_text() -> str:
    return """
    max_selected_context_tokens: 1500
    routes:
      debugging:
        label: Debugging
        keywords: debug, bug, regression
        files: docs/debug.md

      verification:
        label: Verification
        keywords: verify, verification, evidence
        files: docs/verify.md
    """


class ContextRouteSteeringTests(unittest.TestCase):
    def make_repo(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        tempdir = tempfile.TemporaryDirectory()
        root = Path(tempdir.name)
        write_text(root / ".ai-context" / "routing.yml", route_file_text())
        write_text(
            root / "docs" / "debug.md",
            """
            # Debugging

            ## Reproduce

            Reproduce the bug before changing implementation.
            """,
        )
        write_text(
            root / "docs" / "verify.md",
            """
            # Verification

            ## Evidence

            Record verification evidence after the change.
            """,
        )
        self.addCleanup(tempdir.cleanup)
        return tempdir, root

    def run_pack(self, root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [PYTHON, str(PACK_SCRIPT), "--root", str(root), *args],
            cwd=root,
            capture_output=True,
            text=True,
        )

    @staticmethod
    def route_line(stdout: str) -> str:
        return next(line for line in stdout.splitlines() if line.startswith("- Route matches:"))

    def test_automatic_routing_remains_default(self) -> None:
        _, root = self.make_repo()
        result = self.run_pack(root, "debug", "this", "bug")

        self.assertEqual(result.returncode, 0, result.stderr)
        route_line = self.route_line(result.stdout)
        self.assertIn("Debugging", route_line)
        self.assertIn("score=2", route_line)
        self.assertIn("keywords=debug,bug", route_line)
        self.assertNotIn("explicit", route_line)

    def test_explicit_route_is_combined_with_automatic_routes(self) -> None:
        _, root = self.make_repo()
        result = self.run_pack(root, "debug", "this", "bug", "--route", "verification")

        self.assertEqual(result.returncode, 0, result.stderr)
        route_line = self.route_line(result.stdout)
        self.assertIn("Verification [score=1; explicit]", route_line)
        self.assertIn("Debugging [score=2", route_line)
        self.assertLess(route_line.index("Verification"), route_line.index("Debugging"))

    def test_route_only_disables_automatic_routes(self) -> None:
        _, root = self.make_repo()
        result = self.run_pack(
            root,
            "debug",
            "this",
            "bug",
            "--route",
            "verification",
            "--route-only",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        route_line = self.route_line(result.stdout)
        self.assertIn("Verification [score=1; explicit]", route_line)
        self.assertNotIn("Debugging", route_line)
        self.assertIn("docs/verify.md", result.stdout)

    def test_multiple_explicit_routes_preserve_user_order(self) -> None:
        _, root = self.make_repo()
        result = self.run_pack(
            root,
            "prepare",
            "work",
            "--route",
            "verification",
            "--route",
            "debugging",
            "--route-only",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        route_line = self.route_line(result.stdout)
        self.assertLess(route_line.index("Verification"), route_line.index("Debugging"))
        self.assertEqual(route_line.count("explicit"), 2)

    def test_unknown_route_fails_clearly(self) -> None:
        _, root = self.make_repo()
        result = self.run_pack(root, "debug", "bug", "--route", "not_a_route")

        self.assertEqual(result.returncode, 2)
        self.assertIn("unknown route(s): not_a_route", result.stderr)
        self.assertIn("available routes: debugging, verification", result.stderr)

    def test_route_only_requires_explicit_route(self) -> None:
        _, root = self.make_repo()
        result = self.run_pack(root, "debug", "bug", "--route-only")

        self.assertEqual(result.returncode, 2)
        self.assertIn("--route-only requires at least one --route", result.stderr)

    def test_list_routes_does_not_require_task(self) -> None:
        _, root = self.make_repo()
        result = self.run_pack(root, "--list-routes")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout,
            "Available context routes:\n"
            "- debugging: Debugging\n"
            "- verification: Verification\n",
        )


if __name__ == "__main__":
    unittest.main()
