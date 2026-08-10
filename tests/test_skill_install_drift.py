from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

MODULE_PATH = SCRIPTS / "check_skill_install.py"
SPEC = importlib.util.spec_from_file_location("skill_install_drift", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
CHECK = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CHECK
SPEC.loader.exec_module(CHECK)


class SkillInstallDriftTests(unittest.TestCase):
    def make_root(self) -> tempfile.TemporaryDirectory[str]:
        return tempfile.TemporaryDirectory()

    def install_snapshot(
        self,
        root: Path,
        skill: str = "mini-spec",
        *,
        installer: str = "claude-code",
        mutate_before_manifest: bool = False,
    ) -> Path:
        destination = root / skill
        shutil.copytree(CHECK.SKILLS_DIR / skill, destination)
        if mutate_before_manifest:
            (destination / "SKILL.md").write_text("# historical installed skill\n", encoding="utf-8")
        content_hash = CHECK.hash_directory(destination)
        manifest = {
            "schema_version": 1,
            "package": "ai-engineering-skills",
            "installer": installer,
            "skill": skill,
            "source_path": f"skills/{skill}",
            "repo_commit": "abc123",
            "installed_at": "2026-08-01T00:00:00Z",
            "content_hash": f"sha256:{content_hash}",
        }
        (destination / "AI_ENGINEERING_SKILLS_VERSION.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
        return destination

    def evaluate(self, root: Path, *, target: str = "claude"):
        return CHECK.evaluate_install(
            target=target,
            skill_root=root,
            location="user",
            project_path=None,
            skill_names=["mini-spec"],
        )

    def test_clean_snapshot_matching_repo_is_current(self) -> None:
        with self.make_root() as tmp:
            root = Path(tmp)
            self.install_snapshot(root)
            report = self.evaluate(root)
        self.assertEqual(report.status, "CURRENT")
        self.assertEqual(report.skills[0].status, "CURRENT")
        self.assertIsNone(report.repair_command)

    def test_clean_historical_snapshot_is_outdated_and_repairable(self) -> None:
        with self.make_root() as tmp:
            root = Path(tmp)
            self.install_snapshot(root, mutate_before_manifest=True)
            report = self.evaluate(root)
        self.assertEqual(report.status, "DRIFT")
        self.assertEqual(report.skills[0].status, "OUTDATED")
        self.assertIn("--claude-user", report.repair_command or "")
        self.assertIn("--only mini-spec", report.repair_command or "")

    def test_missing_skill_is_drift_and_repairable_when_explicitly_expected(self) -> None:
        with self.make_root() as tmp:
            report = self.evaluate(Path(tmp))
        self.assertEqual(report.status, "DRIFT")
        self.assertEqual(report.skills[0].status, "MISSING")
        self.assertIsNotNone(report.repair_command)

    def test_default_selection_checks_present_skills_not_every_repo_skill(self) -> None:
        with self.make_root() as tmp:
            root = Path(tmp)
            self.install_snapshot(root, "mini-spec")
            with mock.patch.object(
                CHECK,
                "available_skill_names",
                return_value=["mini-spec", "scope-freeze"],
            ):
                selected = CHECK.skills_to_check(None, root)
        self.assertEqual(selected, ["mini-spec"])

    def test_explicit_only_preserves_missing_expectations(self) -> None:
        with self.make_root() as tmp:
            root = Path(tmp)
            with mock.patch.object(
                CHECK,
                "available_skill_names",
                return_value=["mini-spec", "scope-freeze"],
            ):
                selected = CHECK.skills_to_check("mini-spec,scope-freeze", root)
        self.assertEqual(selected, ["mini-spec", "scope-freeze"])

    def test_empty_default_target_requires_explicit_expectation(self) -> None:
        with self.make_root() as tmp, mock.patch.object(
            CHECK,
            "available_skill_names",
            return_value=["mini-spec"],
        ):
            with self.assertRaises(CHECK.InstallerError):
                CHECK.skills_to_check(None, Path(tmp))

    def test_local_edit_takes_precedence_over_repo_drift(self) -> None:
        with self.make_root() as tmp:
            root = Path(tmp)
            destination = self.install_snapshot(root)
            with (destination / "SKILL.md").open("a", encoding="utf-8") as handle:
                handle.write("\n# local customization\n")
            report = self.evaluate(root)
        self.assertEqual(report.status, "DRIFT")
        self.assertEqual(report.skills[0].status, "LOCALLY_MODIFIED")
        self.assertIsNone(report.repair_command)
        self.assertEqual(report.review_required, ("mini-spec",))

    def test_unmanaged_skill_requires_review(self) -> None:
        with self.make_root() as tmp:
            root = Path(tmp)
            destination = root / "mini-spec"
            destination.mkdir()
            (destination / "SKILL.md").write_text("# unmanaged\n", encoding="utf-8")
            report = self.evaluate(root)
        self.assertEqual(report.status, "REVIEW_REQUIRED")
        self.assertEqual(report.skills[0].status, "REVIEW_REQUIRED")
        self.assertIsNone(report.repair_command)

    def test_invalid_manifest_requires_review(self) -> None:
        with self.make_root() as tmp:
            root = Path(tmp)
            destination = root / "mini-spec"
            destination.mkdir()
            (destination / "SKILL.md").write_text("# unmanaged\n", encoding="utf-8")
            (destination / "AI_ENGINEERING_SKILLS_VERSION.json").write_text("{bad", encoding="utf-8")
            report = self.evaluate(root)
        self.assertEqual(report.status, "REVIEW_REQUIRED")
        self.assertEqual(report.skills[0].status, "REVIEW_REQUIRED")

    def test_wrong_installer_manifest_requires_review(self) -> None:
        with self.make_root() as tmp:
            root = Path(tmp)
            self.install_snapshot(root, installer="codex")
            report = self.evaluate(root, target="claude")
        self.assertEqual(report.status, "REVIEW_REQUIRED")
        self.assertIn("expected 'claude-code'", report.skills[0].detail)

    def test_project_repair_command_uses_existing_install_wrapper(self) -> None:
        with self.make_root() as tmp:
            project = Path(tmp).resolve()
            command = CHECK.build_repair_command(
                "codex",
                "project",
                project,
                ["mini-spec", "scope-freeze"],
            )
        self.assertIn("python scripts/aes.py install", command or "")
        self.assertIn("--codex-project", command or "")
        self.assertIn("mini-spec,scope-freeze", command or "")

    def test_review_state_outranks_repairable_drift(self) -> None:
        with self.make_root() as tmp:
            root = Path(tmp)
            modified = self.install_snapshot(root, "mini-spec")
            with (modified / "SKILL.md").open("a", encoding="utf-8") as handle:
                handle.write("\nlocal\n")
            report = CHECK.evaluate_install(
                target="claude",
                skill_root=root,
                location="user",
                project_path=None,
                skill_names=["mini-spec", "scope-freeze"],
            )
        self.assertEqual(report.status, "DRIFT")
        self.assertEqual(
            {result.status for result in report.skills},
            {"LOCALLY_MODIFIED", "MISSING"},
        )
        self.assertIn("scope-freeze", report.repair_command or "")
        self.assertNotIn("--only mini-spec", report.repair_command or "")

    def test_json_output_preserves_per_skill_statuses(self) -> None:
        with self.make_root() as tmp:
            report = self.evaluate(Path(tmp))
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                CHECK.emit_json(report)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["status"], "DRIFT")
        self.assertEqual(payload["skills"][0]["status"], "MISSING")

    def test_main_returns_zero_one_two_for_current_drift_and_review(self) -> None:
        current = CHECK.InstallReport("CURRENT", "claude", "user", "/tmp", (), None, ())
        drift = CHECK.InstallReport("DRIFT", "claude", "user", "/tmp", (), None, ())
        review = CHECK.InstallReport("REVIEW_REQUIRED", "claude", "user", "/tmp", (), None, ())

        cases = [(current, 0), (drift, 1), (review, 2)]
        for report, expected in cases:
            with self.subTest(status=report.status), mock.patch.object(
                CHECK, "resolve_skill_root", return_value=(Path("/tmp"), "user")
            ), mock.patch.object(
                CHECK, "skills_to_check", return_value=["mini-spec"]
            ), mock.patch.object(
                CHECK, "evaluate_install", return_value=report
            ), mock.patch.object(CHECK, "emit_text"):
                self.assertEqual(CHECK.main(["--target", "claude"]), expected)


if __name__ == "__main__":
    unittest.main()
