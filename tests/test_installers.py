from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
SNAPSHOT_DIR = ROOT / "tests" / "snapshots"


def run_command(args: list[str], *, home: Path | None = None, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if home is not None:
        env["HOME"] = str(home)
    return subprocess.run(
        args,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
    )


def normalize_output(text: str, *, home: Path | None = None, project: Path | None = None) -> str:
    normalized = text.replace("\r\n", "\n")
    if home is not None:
        normalized = normalized.replace(str(home), "<HOME>")
    if project is not None:
        normalized = normalized.replace(str(project), "<PROJECT>")
    normalized = re.sub(r"\b\d{8}T\d{6}Z\b", "<UTC_TIMESTAMP>", normalized)
    return normalized.strip()


def read_snapshot(name: str) -> str:
    return (SNAPSHOT_DIR / name).read_text(encoding="utf-8").strip()


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


class InstallerTests(unittest.TestCase):
    maxDiff = None

    def run_claude(self, home: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return run_command([PYTHON, "scripts/install_claude_code.py", *args], home=home)

    def run_codex(self, home: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return run_command([PYTHON, "scripts/install_codex.py", *args], home=home)

    def run_install_sh(self, home: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return run_command(["bash", "install.sh", *args], home=home)

    def make_home(self) -> tempfile.TemporaryDirectory[str]:
        return tempfile.TemporaryDirectory()

    def make_project(self) -> tempfile.TemporaryDirectory[str]:
        return tempfile.TemporaryDirectory()

    def assert_skill_installed(self, target_root: Path, skill_name: str, installer: str) -> Path:
        skill_dir = target_root / skill_name
        self.assertTrue(skill_dir.is_dir(), f"missing skill directory: {skill_dir}")
        manifest = skill_dir / "AI_ENGINEERING_SKILLS_VERSION.json"
        self.assertTrue(manifest.is_file(), f"missing manifest: {manifest}")
        manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual(manifest_data["skill"], skill_name)
        self.assertEqual(manifest_data["installer"], installer)
        self.assertEqual(manifest_data["package"], "ai-engineering-skills")
        return skill_dir

    def assert_template_tree(self, template_root: Path) -> None:
        self.assertTrue(template_root.is_dir(), f"missing template root: {template_root}")
        for filename in ["CONTEXT.md", "SPEC.md", "PLAN.md", "HANDOFF.md"]:
            self.assertTrue((template_root / filename).is_file(), f"missing template file: {template_root / filename}")

    def test_claude_user_dry_run_creates_no_files(self) -> None:
        with self.make_home() as tmp_home:
            home = Path(tmp_home)
            result = self.run_claude(home, "--target", "user", "--dry-run", "--only", "mini-spec,scope-freeze")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((home / ".claude").exists())
            self.assertIn("Would install skill:", result.stdout)
            self.assertIn("/mini-spec", result.stdout)
            self.assertIn("/scope-freeze", result.stdout)

    def test_claude_project_dry_run_creates_no_files(self) -> None:
        with self.make_home() as tmp_home, self.make_project() as tmp_project:
            home = Path(tmp_home)
            project = Path(tmp_project)
            result = self.run_claude(
                home,
                "--target",
                "project",
                "--project-path",
                str(project),
                "--dry-run",
                "--only",
                "mini-spec,scope-freeze",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((project / ".claude").exists())

    def test_codex_user_dry_run_creates_no_files(self) -> None:
        with self.make_home() as tmp_home:
            home = Path(tmp_home)
            result = self.run_codex(home, "--target", "user", "--dry-run", "--only", "mini-spec,scope-freeze")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((home / ".agents").exists())
            self.assertIn("Would install skill:", result.stdout)
            self.assertIn("$mini-spec", result.stdout)
            self.assertIn("$scope-freeze", result.stdout)

    def test_codex_project_dry_run_creates_no_files(self) -> None:
        with self.make_home() as tmp_home, self.make_project() as tmp_project:
            home = Path(tmp_home)
            project = Path(tmp_project)
            result = self.run_codex(
                home,
                "--target",
                "project",
                "--project-path",
                str(project),
                "--dry-run",
                "--only",
                "mini-spec,scope-freeze",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((project / ".agents").exists())

    def test_claude_user_install_selected_skills_and_manifest(self) -> None:
        with self.make_home() as tmp_home:
            home = Path(tmp_home)
            result = self.run_claude(home, "--target", "user", "--only", "mini-spec,scope-freeze")
            self.assertEqual(result.returncode, 0, result.stderr)
            skill_root = home / ".claude" / "skills"
            self.assertEqual(sorted(p.name for p in skill_root.iterdir() if p.is_dir()), ["mini-spec", "scope-freeze"])
            self.assert_skill_installed(skill_root, "mini-spec", "claude-code")
            self.assert_skill_installed(skill_root, "scope-freeze", "claude-code")

    def test_codex_project_install_selected_skills_and_manifest(self) -> None:
        with self.make_home() as tmp_home, self.make_project() as tmp_project:
            home = Path(tmp_home)
            project = Path(tmp_project)
            result = self.run_codex(
                home,
                "--target",
                "project",
                "--project-path",
                str(project),
                "--only",
                "mini-spec,scope-freeze",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            skill_root = project / ".agents" / "skills"
            self.assertEqual(sorted(p.name for p in skill_root.iterdir() if p.is_dir()), ["mini-spec", "scope-freeze"])
            self.assert_skill_installed(skill_root, "mini-spec", "codex")
            self.assert_skill_installed(skill_root, "scope-freeze", "codex")

    def test_only_rejects_unknown_skill(self) -> None:
        with self.make_home() as tmp_home:
            home = Path(tmp_home)
            result = self.run_claude(home, "--target", "user", "--only", "mini-spec,not-a-skill")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unknown skill name(s): not-a-skill", result.stderr)

    def test_reinstall_over_clean_managed_skill_succeeds(self) -> None:
        with self.make_home() as tmp_home:
            home = Path(tmp_home)
            self.assertEqual(self.run_claude(home, "--target", "user", "--only", "mini-spec").returncode, 0)
            result = self.run_claude(home, "--target", "user", "--only", "mini-spec")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Updated managed skill:", result.stdout)

    def test_reinstall_over_modified_managed_skill_fails_without_force(self) -> None:
        with self.make_home() as tmp_home:
            home = Path(tmp_home)
            self.assertEqual(self.run_claude(home, "--target", "user", "--only", "mini-spec").returncode, 0)
            write_text(home / ".claude" / "skills" / "mini-spec" / "SKILL.md", "\n# local edit\n")
            result = self.run_claude(home, "--target", "user", "--only", "mini-spec")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("refusing to overwrite locally modified skill", result.stderr)

    def test_reinstall_over_modified_managed_skill_succeeds_with_force(self) -> None:
        with self.make_home() as tmp_home:
            home = Path(tmp_home)
            self.assertEqual(self.run_claude(home, "--target", "user", "--only", "mini-spec").returncode, 0)
            write_text(home / ".claude" / "skills" / "mini-spec" / "SKILL.md", "\n# local edit\n")
            result = self.run_claude(home, "--target", "user", "--only", "mini-spec", "--force")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Overwrote locally modified skill with --force", result.stdout)

    def test_backup_creates_backup_before_replacement(self) -> None:
        with self.make_home() as tmp_home:
            home = Path(tmp_home)
            self.assertEqual(self.run_claude(home, "--target", "user", "--only", "mini-spec").returncode, 0)
            result = self.run_claude(home, "--target", "user", "--only", "mini-spec", "--backup")
            self.assertEqual(result.returncode, 0, result.stderr)
            backup_root = home / ".claude" / "ai-engineering-skills" / "backups" / "skills"
            backups = sorted(backup_root.glob("mini-spec-*"))
            self.assertTrue(backups, "expected a backup folder")
            self.assertTrue((backups[-1] / "SKILL.md").is_file())
            self.assertIn("Backed up existing skill to:", result.stdout)

    def test_uninstall_removes_managed_selected_skill(self) -> None:
        with self.make_home() as tmp_home:
            home = Path(tmp_home)
            self.assertEqual(self.run_claude(home, "--target", "user", "--only", "mini-spec,scope-freeze").returncode, 0)
            result = self.run_claude(home, "--target", "user", "--uninstall", "--only", "mini-spec")
            self.assertEqual(result.returncode, 0, result.stderr)
            skill_root = home / ".claude" / "skills"
            self.assertFalse((skill_root / "mini-spec").exists())
            self.assertTrue((skill_root / "scope-freeze").exists())

    def test_uninstall_refuses_modified_managed_skill_without_force(self) -> None:
        with self.make_home() as tmp_home:
            home = Path(tmp_home)
            self.assertEqual(self.run_claude(home, "--target", "user", "--only", "mini-spec").returncode, 0)
            write_text(home / ".claude" / "skills" / "mini-spec" / "SKILL.md", "\n# local edit\n")
            result = self.run_claude(home, "--target", "user", "--uninstall", "--only", "mini-spec")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("refusing to remove managed modified skill folder", result.stderr)

    def test_force_uninstall_removes_modified_managed_skill(self) -> None:
        with self.make_home() as tmp_home:
            home = Path(tmp_home)
            self.assertEqual(self.run_claude(home, "--target", "user", "--only", "mini-spec").returncode, 0)
            write_text(home / ".claude" / "skills" / "mini-spec" / "SKILL.md", "\n# local edit\n")
            result = self.run_claude(home, "--target", "user", "--uninstall", "--only", "mini-spec", "--force")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((home / ".claude" / "skills" / "mini-spec").exists())

    def test_include_templates_installs_claude_templates_user(self) -> None:
        with self.make_home() as tmp_home:
            home = Path(tmp_home)
            result = self.run_claude(home, "--target", "user", "--only", "mini-spec", "--include-templates")
            self.assertEqual(result.returncode, 0, result.stderr)
            template_root = home / ".claude" / "ai-engineering-skills" / "templates"
            self.assert_template_tree(template_root)

    def test_include_templates_installs_codex_templates_user(self) -> None:
        with self.make_home() as tmp_home:
            home = Path(tmp_home)
            result = self.run_codex(home, "--target", "user", "--only", "mini-spec", "--include-templates")
            self.assertEqual(result.returncode, 0, result.stderr)
            template_root = home / ".agents" / "ai-engineering-skills" / "templates"
            self.assert_template_tree(template_root)

    def test_include_templates_installs_project_templates(self) -> None:
        with self.make_home() as tmp_home, self.make_project() as tmp_project:
            home = Path(tmp_home)
            project = Path(tmp_project)
            result = self.run_codex(
                home,
                "--target",
                "project",
                "--project-path",
                str(project),
                "--only",
                "mini-spec",
                "--include-templates",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            template_root = project / "docs" / "ai-engineering-skills" / "templates"
            self.assert_template_tree(template_root)

    def test_install_sh_forwards_safety_flags(self) -> None:
        with self.make_home() as tmp_home:
            home = Path(tmp_home)
            self.assertEqual(self.run_install_sh(home, "--claude-user", "--only", "mini-spec").returncode, 0)
            self.assertEqual(
                self.run_install_sh(home, "--claude-user", "--only", "mini-spec", "--backup", "--include-templates").returncode,
                0,
            )
            skill_root = home / ".claude" / "skills"
            self.assert_skill_installed(skill_root, "mini-spec", "claude-code")
            self.assertTrue((home / ".claude" / "ai-engineering-skills" / "templates" / "CONTEXT.md").is_file())
            backup_root = home / ".claude" / "ai-engineering-skills" / "backups" / "skills"
            backups = sorted(backup_root.glob("mini-spec-*"))
            self.assertTrue(backups, "expected a skill backup folder")
            self.assertTrue((backups[-1] / "SKILL.md").is_file())

            write_text(skill_root / "mini-spec" / "SKILL.md", "\n# local edit\n")
            refused = self.run_install_sh(home, "--claude-user", "--only", "mini-spec")
            self.assertNotEqual(refused.returncode, 0)
            self.assertIn("refusing to overwrite locally modified skill", refused.stderr)

            forced = self.run_install_sh(home, "--claude-user", "--only", "mini-spec", "--force")
            self.assertEqual(forced.returncode, 0, forced.stderr)
            uninstalled = self.run_install_sh(home, "--claude-user", "--uninstall", "--only", "mini-spec")
            self.assertEqual(uninstalled.returncode, 0, uninstalled.stderr)
            self.assertFalse((skill_root / "mini-spec").exists())

    def test_install_sh_forwards_codex_dry_run_only(self) -> None:
        with self.make_home() as tmp_home:
            home = Path(tmp_home)
            result = self.run_install_sh(home, "--codex-user", "--dry-run", "--only", "mini-spec")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((home / ".agents").exists())
            self.assertIn("Would install skill:", result.stdout)
            self.assertIn("$mini-spec", result.stdout)

    def test_install_sh_help_snapshot(self) -> None:
        with self.make_home() as tmp_home:
            home = Path(tmp_home)
            result = self.run_install_sh(home, "--help")
            self.assertEqual(result.returncode, 0, result.stderr)
            expected = read_snapshot("install_sh_help.txt")
            self.assertEqual(normalize_output(result.stdout), expected)

    def test_claude_user_dry_run_snapshot(self) -> None:
        with self.make_home() as tmp_home:
            home = Path(tmp_home)
            result = self.run_claude(home, "--target", "user", "--dry-run", "--only", "mini-spec")
            self.assertEqual(result.returncode, 0, result.stderr)
            expected = read_snapshot("install_claude_user_dry_run_only_mini_spec.txt")
            self.assertEqual(normalize_output(result.stdout, home=home), expected)

    def test_codex_user_dry_run_snapshot(self) -> None:
        with self.make_home() as tmp_home:
            home = Path(tmp_home)
            result = self.run_codex(home, "--target", "user", "--dry-run", "--only", "mini-spec")
            self.assertEqual(result.returncode, 0, result.stderr)
            expected = read_snapshot("install_codex_user_dry_run_only_mini_spec.txt")
            self.assertEqual(normalize_output(result.stdout, home=home), expected)


if __name__ == "__main__":
    unittest.main()
