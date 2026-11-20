from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import data_freeze as tool

ROOT = Path(__file__).resolve().parents[1]


class DataFreezeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "data").mkdir()
        (self.root / "data/lift.csv").write_text("group,sales\ncontrol,100\ntreated,120\n")
        (self.root / "analysis.py").write_text(
            "import csv\n"
            "with open('data/lift.csv') as handle:\n"
            "    rows = {row['group']: float(row['sales']) for row in csv.DictReader(handle)}\n"
            "print(round(100 * (rows['treated'] / rows['control'] - 1), 6))\n"
        )
        self.metadata = {"source": "warehouse export as of 2026-11-20",
                         "recipe": "python analysis.py; group=treated/control",
                         "environment": "Python 3.11; stdlib"}
        self.snapshot = self.root / "frozen"

    def freeze(self, output=None, **kwargs):
        return tool.freeze(self.root, output or self.snapshot, ["data/lift.csv"],
                           ["analysis.py"], kwargs or self.metadata)

    def test_exact_copy_stamp_and_late_reproduction_after_live_edit(self):
        report = self.freeze()
        self.assertEqual(report["status"], "PASS")
        archived = self.snapshot / "files"
        original_result = subprocess.check_output(
            [sys.executable, "analysis.py"], cwd=archived, text=True).strip()
        self.assertEqual(original_result, "20.0")
        original = (archived / "data/lift.csv").read_bytes()
        (self.root / "data/lift.csv").write_text("group,sales\ncontrol,110\ntreated,120\n")
        self.assertEqual(tool.check(self.snapshot, None)["status"], "PASS")
        drift = tool.check(self.snapshot, self.root)
        self.assertEqual(drift["status"], "REVIEW_REQUIRED")
        self.assertIn("LIVE_CHANGED: data/lift.csv", drift["issues"])
        self.assertEqual(subprocess.check_output(
            [sys.executable, "analysis.py"], cwd=archived, text=True).strip(), original_result)
        self.assertNotEqual(subprocess.check_output(
            [sys.executable, "analysis.py"], cwd=self.root, text=True).strip(), original_result)
        self.assertEqual((self.snapshot / "files/data/lift.csv").read_bytes(), original)

    def test_stamp_stable_for_identical_capture_and_sensitive_to_recipe(self):
        first = self.freeze()
        same = self.freeze(self.root / "same")
        self.assertEqual(first["stamp"], same["stamp"])
        revised = {**self.metadata, "recipe": "changed denominator"}
        self.assertNotEqual(first["stamp"], self.freeze(self.root / "revised", **revised)["stamp"])

    def test_diff_reports_data_context_metadata_added_and_removed(self):
        self.freeze()
        (self.root / "data/lift.csv").write_text("group,sales\ncontrol,100\ntreated,130\n")
        (self.root / "analysis.py").write_text("lift = 130 / 100 - 1\n")
        (self.root / "params.json").write_text('{"window": 30}\n')
        second = self.root / "second"
        tool.freeze(self.root, second, ["data/lift.csv"], ["params.json"],
                    {**self.metadata, "recipe": "python analysis.py --window 30"})
        result = tool.compare(self.snapshot, second, True)
        changes = {r["path"]: r for r in result["changes"]}
        self.assertEqual(changes["analysis.py"]["change"], "removed")
        self.assertEqual(changes["params.json"]["change"], "added")
        self.assertIn("-treated,120", changes["data/lift.csv"]["text_diff"])
        self.assertIn("+treated,130", changes["data/lift.csv"]["text_diff"])
        self.assertIn("recipe", result["metadata_changes"])

    def test_integrity_rejects_tampered_missing_data_and_changed_manifest(self):
        self.freeze()
        copied = self.snapshot / "files/data/lift.csv"
        copied.write_bytes(b"tampered")
        self.assertEqual(tool.check(self.snapshot, None)["status"], "REVIEW_REQUIRED")
        self.assertEqual(tool.compare(self.snapshot, self.snapshot, False)["status"],
                         "REVIEW_REQUIRED")
        copied.unlink()
        self.assertIn("MISSING: data/lift.csv", tool.check(self.snapshot, None)["issues"])
        path = self.snapshot / "manifest.json"
        data = json.loads(path.read_text())
        data["recipe"] = "unrecorded change"
        path.write_text(json.dumps(data))
        self.assertIn("STAMP_MISMATCH", tool.check(self.snapshot, None)["issues"])

    def test_existing_snapshot_never_overwritten_and_no_automatic_discovery(self):
        (self.root / ".env").write_text("PRIVATE=secret\n")
        self.freeze()
        before = (self.snapshot / "manifest.json").read_bytes()
        with self.assertRaises(ValueError):
            self.freeze()
        self.assertEqual((self.snapshot / "manifest.json").read_bytes(), before)
        self.assertFalse((self.snapshot / "files/.env").exists())

    def test_invalid_paths_duplicate_and_missing_sources_leave_no_snapshot(self):
        for name in ("../private", "/absolute", "data/../lift.csv", "C:/data.csv",
                     "data\\lift.csv", "missing.csv"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                tool.freeze(self.root, self.snapshot, [name], [], self.metadata)
            self.assertFalse(self.snapshot.exists())
        with self.assertRaises(ValueError):
            tool.freeze(self.root, self.snapshot, ["data/lift.csv"],
                        ["data/lift.csv"], self.metadata)

    def test_symlink_sources_snapshot_files_and_outputs_rejected(self):
        (self.root / "link.csv").symlink_to(self.root / "data/lift.csv")
        with self.assertRaises(ValueError):
            tool.freeze(self.root, self.snapshot, ["link.csv"], [], self.metadata)
        alias = self.root / "alias"
        alias.symlink_to(self.root / "data", target_is_directory=True)
        with self.assertRaises(ValueError):
            tool.freeze(self.root, alias / "freeze", ["data/lift.csv"], [], self.metadata)
        self.freeze()
        copied = self.snapshot / "files/data/lift.csv"
        copied.unlink()
        copied.symlink_to(self.root / "data/lift.csv")
        with self.assertRaises(ValueError):
            tool.check(self.snapshot, None)
        copied.unlink()
        (self.snapshot / "files/data").rmdir()
        (self.snapshot / "files/analysis.py").unlink()
        (self.snapshot / "files").rmdir()
        (self.snapshot / "files").symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ValueError):
            tool.check(self.snapshot, None)

    def test_copy_failure_cleans_partial_snapshot(self):
        with mock.patch.object(tool.shutil, "copyfileobj", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                self.freeze()
        self.assertFalse(self.snapshot.exists())

    def test_changing_source_during_capture_cleans_snapshot(self):
        original = tool.shutil.copyfileobj
        def mutate(reader, writer):
            original(reader, writer)
            (self.root / "analysis.py").write_text("changed during copy")
        with mock.patch.object(tool.shutil, "copyfileobj", side_effect=mutate):
            with self.assertRaises(ValueError):
                self.freeze()
        self.assertFalse(self.snapshot.exists())

    def test_invalid_schema_paths_hashes_and_empty_inputs_rejected(self):
        self.freeze()
        path = self.snapshot / "manifest.json"
        original = json.loads(path.read_text())
        for change in (
            {"schema_version": True}, {"files": []}, {"source": ""},
            {"files": [{**original["files"][0], "path": "../escape"}]},
            {"files": [{**original["files"][0], "bytes": True}]},
            {"files": [original["files"][0], original["files"][0]]},
        ):
            with self.subTest(change=change):
                path.write_text(json.dumps({**original, **change}))
                with self.assertRaises(ValueError):
                    tool.check(self.snapshot, None)

    def test_binary_and_large_text_diffs_are_bounded(self):
        (self.root / "data/lift.csv").write_bytes(b"\x00one")
        self.freeze()
        (self.root / "data/lift.csv").write_bytes(b"\x00two")
        second = self.root / "second"
        self.freeze(second)
        result = tool.compare(self.snapshot, second, True)
        self.assertIn("binary", result["changes"][0]["text_diff_skipped"])
        (self.root / "data/lift.csv").write_bytes(b"x" * 128001)
        third = self.root / "third"
        self.freeze(third)
        self.assertIn("exceeds", tool.compare(second, third, True)["changes"][0]["text_diff_skipped"])

    def test_cli_dispatch_and_status_codes(self):
        cli = [sys.executable, str(ROOT / "scripts/aes.py"), "data", "--format", "json"]
        capture = subprocess.run(cli + ["freeze", "--root", str(self.root),
            "--input", "data/lift.csv", "--context", "analysis.py",
            "--output", str(self.snapshot),
            "--source", self.metadata["source"], "--recipe", self.metadata["recipe"],
            "--environment", self.metadata["environment"]], capture_output=True, text=True)
        self.assertEqual(capture.returncode, 0, capture.stderr)
        self.assertEqual(json.loads(capture.stdout)["status"], "PASS")
        (self.root / "analysis.py").write_text("revised")
        drift = subprocess.run(cli + ["check", str(self.snapshot), "--live-root", str(self.root)],
                               capture_output=True, text=True)
        self.assertEqual(drift.returncode, 3, drift.stderr)
        missing = subprocess.run(cli + ["check", str(self.root / "missing")],
                                 capture_output=True, text=True)
        self.assertEqual(missing.returncode, 2)


if __name__ == "__main__":
    unittest.main()
