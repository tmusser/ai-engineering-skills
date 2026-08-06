from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "scope_gate.py"

SPEC = importlib.util.spec_from_file_location("scope_gate", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
GATE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GATE
SPEC.loader.exec_module(GATE)


def run(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args),
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )


def write_scope(
    root: Path,
    *,
    allowed: tuple[str, ...] = ("src/**", "tests/**"),
    read_only: tuple[str, ...] = ("docs/**",),
    forbidden: tuple[str, ...] = (".env",),
    review: tuple[str, ...] = (),
    max_files: int | None = None,
    renames: bool | None = None,
    deletions: bool | None = None,
) -> None:
    lines = [
        "SCOPE FREEZE",
        "Task: add bounded parser behavior",
        "Allowed writes:",
        *(f"- {item}" for item in allowed),
        "Read-only:",
        *(f"- {item}" for item in read_only),
        "Forbidden:",
        *(f"- {item}" for item in forbidden),
        "Review required if:",
        *(f"- {item}" for item in review),
    ]
    if max_files is not None:
        lines.append(f"Max files changed: {max_files}")
    if renames is not None:
        lines.append(f"Renames allowed: {'yes' if renames else 'no'}")
    if deletions is not None:
        lines.append(f"Deletions allowed: {'yes' if deletions else 'no'}")
    lines.extend(
        [
            "Stop when: parser behavior and focused tests are complete",
            "Invalid if: any write escapes the declared paths",
            "",
        ]
    )
    (root / "SCOPE.md").write_text("\n".join(lines), encoding="utf-8")


class Repo:
    def __init__(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        run("git", "init", "-q", cwd=self.root)
        run("git", "config", "user.email", "scope@example.com", cwd=self.root)
        run("git", "config", "user.name", "Scope Test", cwd=self.root)
        (self.root / "src").mkdir()
        (self.root / "tests").mkdir()
        (self.root / "docs").mkdir()
        (self.root / "src" / "parser.py").write_text("VALUE = 1\n", encoding="utf-8")
        (self.root / "tests" / "test_parser.py").write_text(
            "def test_value():\n    assert True\n", encoding="utf-8"
        )
        (self.root / "docs" / "guide.md").write_text("# Guide\n", encoding="utf-8")
        write_scope(self.root)
        run("git", "add", ".", cwd=self.root)
        run("git", "commit", "-qm", "initial", cwd=self.root)
        self.base = run("git", "rev-parse", "HEAD", cwd=self.root).stdout.strip()

    def close(self) -> None:
        self.tmp.cleanup()


class ScopeGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = Repo()

    def tearDown(self) -> None:
        self.repo.close()

    def evaluate(self):
        return GATE.evaluate(self.repo.root, self.repo.base, Path("SCOPE.md"))

    def test_in_scope_change_passes(self) -> None:
        (self.repo.root / "src" / "parser.py").write_text("VALUE = 2\n", encoding="utf-8")
        result = self.evaluate()
        self.assertEqual(result.status, "PASS")
        self.assertEqual(result.failures, ())

    def test_untracked_in_scope_file_passes(self) -> None:
        (self.repo.root / "src" / "new_parser.py").write_text("VALUE = 2\n", encoding="utf-8")
        result = self.evaluate()
        self.assertEqual(result.status, "PASS")
        self.assertEqual(result.changed_files[0].status, "A")

    def test_out_of_scope_change_fails(self) -> None:
        (self.repo.root / "README.md").write_text("# surprise\n", encoding="utf-8")
        result = self.evaluate()
        self.assertEqual(result.status, "FAIL")
        self.assertTrue(any("out-of-scope write" in item for item in result.failures))

    def test_read_only_change_fails(self) -> None:
        (self.repo.root / "docs" / "guide.md").write_text("# Changed\n", encoding="utf-8")
        result = self.evaluate()
        self.assertEqual(result.status, "FAIL")
        self.assertTrue(any("read-only path modified" in item for item in result.failures))

    def test_forbidden_change_fails(self) -> None:
        (self.repo.root / ".env").write_text("TOKEN=nope\n", encoding="utf-8")
        result = self.evaluate()
        self.assertEqual(result.status, "FAIL")
        self.assertTrue(any("forbidden write" in item for item in result.failures))

    def test_review_trigger_is_not_silently_passed(self) -> None:
        write_scope(self.repo.root, review=("tests changed",))
        run("git", "add", "SCOPE.md", cwd=self.repo.root)
        run("git", "commit", "-qm", "scope", cwd=self.repo.root)
        self.repo.base = run("git", "rev-parse", "HEAD", cwd=self.repo.root).stdout.strip()
        (self.repo.root / "tests" / "test_parser.py").write_text(
            "def test_value():\n    assert 1 == 1\n", encoding="utf-8"
        )
        result = self.evaluate()
        self.assertEqual(result.status, "REVIEW_REQUIRED")
        self.assertIn("tests changed: tests/test_parser.py", result.review_required)

    def test_explicit_review_path_pattern_is_supported(self) -> None:
        (self.repo.root / ".github" / "workflows").mkdir(parents=True)
        (self.repo.root / ".github" / "workflows" / "ci.yml").write_text(
            "name: ci\n", encoding="utf-8"
        )
        write_scope(
            self.repo.root,
            allowed=("src/**", "tests/**", ".github/workflows/**"),
            review=(".github/workflows/**",),
        )
        result = self.evaluate()
        self.assertEqual(result.status, "REVIEW_REQUIRED")

    def test_changed_file_budget_is_enforced(self) -> None:
        write_scope(self.repo.root, max_files=1)
        run("git", "add", "SCOPE.md", cwd=self.repo.root)
        run("git", "commit", "-qm", "scope", cwd=self.repo.root)
        self.repo.base = run("git", "rev-parse", "HEAD", cwd=self.repo.root).stdout.strip()
        (self.repo.root / "src" / "parser.py").write_text("VALUE = 2\n", encoding="utf-8")
        (self.repo.root / "tests" / "test_parser.py").write_text(
            "def test_value():\n    assert True\n# changed\n", encoding="utf-8"
        )
        result = self.evaluate()
        self.assertEqual(result.status, "FAIL")
        self.assertTrue(any("budget exceeded" in item for item in result.failures))

    def test_rename_and_delete_policies_are_enforced(self) -> None:
        write_scope(
            self.repo.root,
            allowed=("src/**", "tests/**"),
            renames=False,
            deletions=False,
        )
        run("git", "add", "SCOPE.md", cwd=self.repo.root)
        run("git", "commit", "-qm", "scope", cwd=self.repo.root)
        self.repo.base = run("git", "rev-parse", "HEAD", cwd=self.repo.root).stdout.strip()
        run("git", "mv", "src/parser.py", "src/reader.py", cwd=self.repo.root)
        run("git", "rm", "tests/test_parser.py", cwd=self.repo.root)
        result = self.evaluate()
        self.assertEqual(result.status, "FAIL")
        self.assertTrue(any("rename not allowed" in item for item in result.failures))
        self.assertTrue(any("deletion not allowed" in item for item in result.failures))

    def test_missing_or_malformed_scope_requires_review(self) -> None:
        (self.repo.root / "SCOPE.md").unlink()
        missing = self.evaluate()
        self.assertEqual(missing.status, "REVIEW_REQUIRED")

        (self.repo.root / "SCOPE.md").write_text("SCOPE FREEZE\nTask: _TBD_\n", encoding="utf-8")
        malformed = self.evaluate()
        self.assertEqual(malformed.status, "REVIEW_REQUIRED")
        self.assertTrue(any("invalid scope contract" in item for item in malformed.review_required))

    def test_non_path_forbidden_operation_is_advisory_not_fake_enforcement(self) -> None:
        write_scope(self.repo.root, forbidden=("do not refactor adjacent code",))
        contract, errors = GATE.parse_scope(
            (self.repo.root / "SCOPE.md").read_text(encoding="utf-8")
        )
        self.assertEqual(errors, ())
        assert contract is not None
        self.assertEqual(contract.forbidden, ())
        self.assertTrue(any("advisory only" in warning for warning in contract.warnings))

    def test_cli_json_and_exit_codes(self) -> None:
        (self.repo.root / "README.md").write_text("# surprise\n", encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--root",
                str(self.repo.root),
                "--base",
                self.repo.base,
                "--format",
                "json",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "FAIL")
        self.assertEqual(payload["changed_files"][0]["path"], "README.md")


if __name__ == "__main__":
    unittest.main()
