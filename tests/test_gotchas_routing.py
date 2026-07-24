from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
BUILD_SCRIPT = ROOT / "scripts" / "build_context_index.py"
PACK_SCRIPT = ROOT / "scripts" / "context_pack.py"
ROUTING_FILE = ROOT / ".ai-context" / "routing.yml"
GOTCHAS_TEMPLATE = ROOT / "templates" / "GOTCHAS.md"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run_script(script: Path, *args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, str(script), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


class GotchasRoutingTests(unittest.TestCase):
    maxDiff = None

    def make_repo(self, files: dict[str, str]) -> Path:
        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        root = Path(tempdir.name)
        write_text(root / ".ai-context/routing.yml", ROUTING_FILE.read_text(encoding="utf-8"))
        for relative, content in files.items():
            write_text(root / relative, content)
        return root

    def build(self, root: Path) -> subprocess.CompletedProcess[str]:
        return run_script(BUILD_SCRIPT, "--root", str(root), cwd=root)

    def pack(self, root: Path, task: str, *extra: str) -> subprocess.CompletedProcess[str]:
        return run_script(PACK_SCRIPT, "--root", str(root), task, *extra, cwd=root)

    def test_live_gotchas_route_outranks_template(self) -> None:
        root = self.make_repo(
            {
                "GOTCHAS.md": """# Gotchas\n\n## G1 - Export footgun\n\n- Trigger: editing export filters\n- Gotcha: live project sharp edge\n- Consequence: wrong rows\n- Safe path: run the boundary fixture\n- Evidence: tests/test_export.py\n- Last verified: 2026-07-24\n- Status: active\n""",
                "templates/GOTCHAS.md": GOTCHAS_TEMPLATE.read_text(encoding="utf-8"),
            }
        )
        self.assertEqual(self.build(root).returncode, 0)
        result = self.pack(root, "inspect gotchas and sharp edges before editing export")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Gotchas / sharp edges", result.stdout)
        self.assertIn("live project sharp edge", result.stdout)
        self.assertLess(
            result.stdout.index("| other | GOTCHAS.md"),
            result.stdout.index("| template | templates/GOTCHAS.md"),
        )

    def test_require_file_records_gotchas_in_packet_integrity(self) -> None:
        root = self.make_repo(
            {
                "GOTCHAS.md": """# Gotchas\n\n## G1 - Resume trap\n\n- Trigger: resume\n- Gotcha: check the compatibility shim first\n- Consequence: regression\n- Safe path: inspect shim.py\n- Evidence: tests/test_shim.py\n- Last verified: 2026-07-24\n- Status: active\n""",
                "HANDOFF.md": "# Handoff\n\n## Resume packet\n\nContinue safely.\n",
            }
        )
        self.assertEqual(self.build(root).returncode, 0)
        result = self.pack(
            root,
            "resume this task safely",
            "--require-file",
            "GOTCHAS.md",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Required sources: GOTCHAS.md=represented", result.stdout)
        self.assertIn("| required | GOTCHAS.md", result.stdout)

    def test_unrelated_task_does_not_force_gotchas_route(self) -> None:
        root = self.make_repo(
            {
                "SPEC.md": "# Spec\n\n## Objective\n\nPlan the small feature.\n",
                "GOTCHAS.md": "# Gotchas\n\n## G1\n\nUnrelated sharp edge.\n",
            }
        )
        self.assertEqual(self.build(root).returncode, 0)
        result = self.pack(root, "plan this small feature")
        self.assertEqual(result.returncode, 0, result.stderr)
        route_line = next(
            line for line in result.stdout.splitlines() if line.startswith("- Route matches:")
        )
        self.assertNotIn("Gotchas / sharp edges", route_line)


if __name__ == "__main__":
    unittest.main()
