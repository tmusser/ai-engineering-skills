"""Exercise POSIX wrapper dispatch without writing real skill installations."""
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("sh"), "POSIX shell required")
class InstallWrapperTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        self.checkout = root / "repo with spaces"
        self.checkout.mkdir()
        shutil.copy2(ROOT / "install.sh", self.checkout / "install.sh")
        scripts = self.checkout / "scripts"
        scripts.mkdir()
        for name in ("install_claude_code.py", "install_codex.py"):
            (scripts / name).write_text(
                "import json, os, sys\n"
                "print(json.dumps([os.path.basename(__file__), os.getcwd(), *sys.argv[1:]]))\n",
                encoding="utf-8",
            )
        self.project = root / "target project"
        self.project.mkdir()

    def invoke(self, *args):
        return subprocess.run(
            ["sh", str(self.checkout / "install.sh"), *args],
            cwd=self.project, capture_output=True, text=True, timeout=15,
        )

    def test_out_of_tree_and_both_value_syntaxes(self):
        for target, script in (("claude", "install_claude_code.py"),
                               ("codex", "install_codex.py")):
            for args in ((f"--{target}-project", ".", "--only", "mini-spec,scope-freeze"),
                         (f"--{target}-project=.", "--only=mini-spec,scope-freeze"),
                         (f"--{target}-project={self.project}", "--only=mini-spec,scope-freeze")):
                with self.subTest(args=args):
                    result = self.invoke(*args, "--dry-run")
                    self.assertEqual(result.returncode, 0, result.stderr)
                    path = str(self.project) if args[0].endswith(str(self.project)) else "."
                    self.assertEqual(json.loads(result.stdout), [
                        script, str(self.project.resolve()), "--target", "project",
                        "--project-path", path, "--dry-run", "--only", "mini-spec,scope-freeze",
                    ])

    def test_default_and_explicit_user_targets(self):
        for args, script in (((), "install_claude_code.py"),
                             (("--claude-user",), "install_claude_code.py"),
                             (("--codex-user",), "install_codex.py")):
            with self.subTest(args=args):
                result = self.invoke(*args, "--dry-run", "--backup", "--uninstall", "--force",
                                     "--include-templates", "--only=mini-spec")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout), [
                    script, str(self.project.resolve()), "--target", "user", "--dry-run",
                    "--backup", "--uninstall", "--force", "--only", "mini-spec", "--include-templates",
                ])

    def test_missing_empty_and_option_like_values(self):
        for flag in ("--only", "--claude-project", "--codex-project"):
            for args in ((flag,), (flag, "--dry-run"), (flag, ""), (flag + "=",),
                         (flag + "=--dry-run",)):
                with self.subTest(args=args):
                    result = self.invoke(*args)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(f"{flag} requires", result.stderr)
                    self.assertEqual(result.stdout, "")

    def test_multiple_targets_are_rejected(self):
        targets = (("--claude-user",), ("--claude-project", "."),
                   ("--codex-user",), ("--codex-project=.",))
        for first in targets:
            for second in targets:
                with self.subTest(first=first, second=second):
                    result = self.invoke(*first, *second)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("conflicting target flags", result.stderr)
                    self.assertEqual(result.stdout, "")

    def test_unknown_option(self):
        result = self.invoke("--not-an-option")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown option", result.stderr)
        self.assertEqual(result.stdout, "")
