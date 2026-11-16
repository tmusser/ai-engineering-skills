from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "scripts" / "file_ledger.py"


class FileLedgerTests(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.ledger = self.root / ".ai-context/file-ledger.json"
        (self.root / "src").mkdir()
        (self.root / "tests").mkdir()
        self.write("SPEC.md", "# Spec\n\n## Acceptance criteria\n\n- Preserve CSV headers.\n")
        self.write("src/export.py", "def export():\n    return 'order_id,region\\n'\n")
        self.write("tests/test_export.py", "def test_export():\n    assert True\n")
        self.write("README.md", "# Usage\n\nCSV export and setup instructions.\n")

    def write(self, name: str, text: str) -> None:
        target = self.root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    def cmd(self, *args: str, fmt: str = "json"):
        process = subprocess.run(
            [sys.executable, str(TOOL), "--root", str(self.root),
             "--format", fmt, *args],
            text=True, capture_output=True, check=False,
        )
        return process, json.loads(process.stdout) if process.stdout and fmt == "json" else None

    def proposal(self) -> dict:
        run, result = self.cmd(
            "propose", "--path", "src/export.py", "--path", "tests/test_export.py",
            "--path", "SPEC.md",
        )
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(result["status"], "PROPOSED")
        return json.loads(self.ledger.read_text(encoding="utf-8"))

    def approve(self) -> dict:
        data = self.proposal()
        for row in data["entries"]:
            if row["path"] == "src/export.py":
                row["purpose"] = "Implements CSV export behavior"
                row["use_when"] = ["csv export", "empty results"]
                row["related"] = ["tests/test_export.py"]
            elif row["path"] == "tests/test_export.py":
                row["purpose"] = "Regression tests for CSV export"
                row["use_when"] = ["export tests", "verification"]
                row["related"] = ["src/export.py"]
            else:
                row["purpose"] = "Task acceptance contract for CSV export"
                row["use_when"] = ["acceptance contract", "scope"]
        data["approved"] = True
        self.ledger.write_text(json.dumps(data), encoding="utf-8")
        return data

    def test_absent_ledger_is_optional_for_check_but_query_requires_review(self) -> None:
        check, report = self.cmd("check")
        self.assertEqual(check.returncode, 0)
        self.assertEqual(report["status"], "NOT_APPLICABLE")
        query, result = self.cmd("query", "csv", "export")
        self.assertEqual(query.returncode, 3)
        self.assertEqual(result["matches"], [])

    def test_proposal_is_unapproved_metadata_only_and_deterministic(self) -> None:
        data = self.proposal()
        self.assertEqual(data["schema_version"], 1)
        self.assertIs(data["approved"], False)
        self.assertEqual([row["path"] for row in data["entries"]],
                         ["SPEC.md", "src/export.py", "tests/test_export.py"])
        self.assertEqual([row["kind"] for row in data["entries"]],
                         ["contract", "implementation", "test"])
        for row in data["entries"]:
            self.assertEqual(row["purpose"], "")
            self.assertEqual(row["use_when"], [])
            self.assertEqual(row["related"], [])
            self.assertRegex(row["sha256"], r"^sha256:[0-9a-f]{64}$")
        self.assertNotIn("def export()", self.ledger.read_text(encoding="utf-8"))
        query, result = self.cmd("query", "csv", "export")
        self.assertEqual(query.returncode, 3)
        self.assertEqual(result["matches"], [])

    def test_approved_query_returns_small_fresh_lookup_without_source_content(self) -> None:
        self.approve()
        proc, report = self.cmd("query", "csv", "export", "--limit", "2")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(len(report["matches"]), 2)
        self.assertEqual(report["matches"][0]["path"], "src/export.py")
        self.assertEqual(report["matches"][0]["freshness"], "CURRENT")
        self.assertEqual(report["matches"][0]["related"], ["tests/test_export.py"])
        self.assertNotIn("return 'order_id", proc.stdout)
        self.assertIn("Navigation only", report["scope"])
        all_status, check = self.cmd("check")
        self.assertEqual(all_status.returncode, 0)
        self.assertEqual(len(check["matches"]), 3)

    def test_unrelated_file_change_does_not_invalidate_a_focused_lookup(self) -> None:
        self.approve()
        self.write("tests/test_export.py", "def test_export():\n    assert False\n")
        lookup, report = self.cmd("query", "empty", "results", "--limit", "1")
        self.assertEqual(lookup.returncode, 0, report)
        self.assertEqual([row["path"] for row in report["matches"]], ["src/export.py"])
        check, result = self.cmd("check")
        self.assertEqual(check.returncode, 3)
        self.assertTrue(any("STALE" in warning for warning in result["warnings"]))

    def test_stale_or_deleted_matching_source_cannot_be_trusted(self) -> None:
        self.approve()
        self.write("src/export.py", "def export():\n    return ''\n")
        stale, report = self.cmd("query", "empty", "results")
        self.assertEqual(stale.returncode, 3, report)
        self.assertEqual(report["matches"][0]["freshness"], "STALE")
        (self.root / "src/export.py").unlink()
        missing, report = self.cmd("query", "empty", "results")
        self.assertEqual(missing.returncode, 3)
        self.assertEqual(report["matches"][0]["freshness"], "MISSING")

    def test_reviewed_purpose_and_use_when_are_required(self) -> None:
        data = self.proposal()
        data["approved"] = True
        self.ledger.write_text(json.dumps(data), encoding="utf-8")
        proc, result = self.cmd("check")
        self.assertEqual(proc.returncode, 3)
        self.assertTrue(any("not reviewed" in warning for warning in result["warnings"]))

    def test_global_approval_requires_all_entries_even_for_narrow_lookup(self) -> None:
        data = self.approve()
        other = next(row for row in data["entries"] if row["path"] == "tests/test_export.py")
        other["use_when"] = []
        self.ledger.write_text(json.dumps(data), encoding="utf-8")
        proc, report = self.cmd("query", "empty", "results", "--limit", "1")
        self.assertEqual(proc.returncode, 3, report)
        self.assertTrue(any("tests/test_export.py: use_when tags not reviewed" in warning
                            for warning in report["warnings"]))

    def test_missing_related_file_requires_review(self) -> None:
        data = self.approve()
        source = next(row for row in data["entries"] if row["path"] == "src/export.py")
        source["related"] = ["tests/missing_export.py"]
        self.ledger.write_text(json.dumps(data), encoding="utf-8")
        proc, report = self.cmd("query", "empty", "results")
        self.assertEqual(proc.returncode, 3, report)
        self.assertIn("related path missing", str(report["warnings"]))

    def test_symlink_output_cannot_escape_or_be_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as outside:
            external = Path(outside) / "captured.json"
            self.ledger.parent.mkdir()
            self.ledger.symlink_to(external)
            proc, _ = self.cmd("propose", "--path", "SPEC.md")
            self.assertEqual(proc.returncode, 2)
            self.assertFalse(external.exists())

    def test_missing_matches_or_noninformative_query_do_not_fake_success(self) -> None:
        self.approve()
        missing, report = self.cmd("query", "quantum", "database")
        self.assertEqual(missing.returncode, 3)
        self.assertEqual(report["matches"], [])
        bad, _ = self.cmd("query", "the", "and", "in")
        self.assertEqual(bad.returncode, 2)
        self.assertIn("meaningful", bad.stderr)

    def test_bad_paths_schema_and_duplicates_are_input_errors(self) -> None:
        data = self.approve()
        for mutated in (
            {**data, "schema_version": 2},
            {**data, "approved": "yes"},
            {**data, "extra": "unrecognized"},
            {**data, "entries": [*data["entries"], data["entries"][0]]},
            {**data, "entries": [{**data["entries"][0], "path": "../secrets.md"}]},
            {**data, "entries": [{**data["entries"][0], "kind": []}]},
        ):
            with self.subTest(mutated=str(mutated)[:100]):
                self.ledger.write_text(json.dumps(mutated), encoding="utf-8")
                proc, _ = self.cmd("check")
                self.assertEqual(proc.returncode, 2, proc.stderr)

    def test_prevents_symlink_file_and_symlink_parent(self) -> None:
        with tempfile.TemporaryDirectory() as outside:
            external = Path(outside) / "secret.py"
            external.write_text("do not index\n", encoding="utf-8")
            (self.root / "src/link.py").symlink_to(external)
            (self.root / "linked").symlink_to(Path(outside), target_is_directory=True)
            for path in ("src/link.py", "linked/secret.py"):
                with self.subTest(path=path):
                    proc, _ = self.cmd("propose", "--path", path)
                    self.assertEqual(proc.returncode, 2, proc.stderr)
                    self.assertIn("symlink", proc.stderr)

    def test_proposal_never_overwrites_reviewed_annotations(self) -> None:
        data = self.approve()
        first = self.ledger.read_bytes()
        proc, _ = self.cmd("propose", "--path", "README.md")
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(self.ledger.read_bytes(), first)
        self.assertTrue(data["approved"])

    def test_repropose_preserves_metadata_but_resets_approval_on_hash_change(self) -> None:
        self.approve()
        self.write("src/export.py", "# modified\n")
        result, report = self.cmd("propose", "--from-ledger",
                                  ".ai-context/file-ledger.json", "--output",
                                  ".ai-context/file-ledger.next.json")
        self.assertEqual(result.returncode, 0, result.stderr)
        revised = json.loads((self.root / ".ai-context/file-ledger.next.json").read_text())
        self.assertIs(revised["approved"], False)
        source = next(row for row in revised["entries"] if row["path"] == "src/export.py")
        self.assertEqual(source["purpose"], "Implements CSV export behavior")
        self.assertEqual(source["use_when"], ["csv export", "empty results"])
        actual = hashlib.sha256((self.root / "src/export.py").read_bytes()).hexdigest()
        self.assertEqual(source["sha256"], "sha256:" + actual)

    def test_tracked_discovery_ignores_untracked_secrets_and_binary_noise(self) -> None:
        def git(*args: str):
            return subprocess.run(["git", *args], cwd=self.root,
                                  capture_output=True, text=True, check=True)
        git("init", "-q")
        self.write(".env", "PRIVATE=1")
        self.write("notes.py", "# untracked and should not appear\n")
        self.write("assets/picture.png", "opaque data")
        git("add", "SPEC.md", "src/export.py", "tests/test_export.py",
            ".env", "assets/picture.png")
        proc, report = self.cmd("propose", "--tracked")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        ledger = json.loads(self.ledger.read_text())
        paths = {row["path"] for row in ledger["entries"]}
        self.assertEqual(paths, {"SPEC.md", "src/export.py", "tests/test_export.py"})
        self.assertNotIn("PRIVATE=1", self.ledger.read_text())

    def test_query_limit_rejected_if_out_of_range(self) -> None:
        self.approve()
        for limit in ("0", "21"):
            with self.subTest(limit=limit):
                proc, _ = self.cmd("query", "export", "--limit", limit)
                self.assertEqual(proc.returncode, 2)


if __name__ == "__main__":
    unittest.main()
