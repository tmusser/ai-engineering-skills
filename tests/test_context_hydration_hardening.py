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
BUILD_SCRIPT = ROOT / "scripts" / "build_context_index.py"
PACK_SCRIPT = ROOT / "scripts" / "context_pack.py"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text).lstrip("\n"), encoding="utf-8")


def run_script(script: Path, *args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, str(script), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def route_text(max_tokens: int = 1500) -> str:
    return f"""
    max_selected_context_tokens: {max_tokens}
    routes:
      context_hydration:
        label: Context hydration
        keywords: context hydration, context packet, context index, context librarian, working-context headroom, hydrate, hydration
        files: docs/context-hydration.md, scripts/context_pack.py, scripts/build_context_index.py, .ai-context/routing.yml, tests/test_context_hydration.py

      resume_handoff:
        label: Resume / handoff
        keywords: handoff, resume, fresh context, resume packet, continuation
        files: HANDOFF.md, CONTEXT.md, templates/HANDOFF.md, skills/handoff/SKILL.md

      verification:
        label: Verification
        keywords: verify, verification, evidence, review required, review_required
        files: VERIFY.md, SPEC.md, templates/VERIFY.md, skills/verify-contract/SKILL.md
    """


class ContextHydrationHardeningTests(unittest.TestCase):
    maxDiff = None

    def make_repo(self, files: dict[str, str]) -> Path:
        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        root = Path(tempdir.name)
        write_text(root / ".ai-context/routing.yml", route_text())
        for relative, content in files.items():
            write_text(root / relative, content)
        return root

    def build(self, root: Path) -> subprocess.CompletedProcess[str]:
        return run_script(BUILD_SCRIPT, "--root", str(root), cwd=root)

    def pack(self, root: Path, task: str, *extra: str) -> subprocess.CompletedProcess[str]:
        return run_script(PACK_SCRIPT, "--root", str(root), task, *extra, cwd=root)

    def test_live_handoff_outranks_template(self) -> None:
        root = self.make_repo(
            {
                "HANDOFF.md": """
                    # Handoff
                    ## Resume packet
                    Live state wins.
                """,
                "templates/HANDOFF.md": """
                    # Handoff template
                    ## Resume packet
                    Template fallback.
                """,
            }
        )
        self.assertEqual(self.build(root).returncode, 0)
        result = self.pack(root, "resume handoff")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertLess(
            result.stdout.index("| current_state | HANDOFF.md"),
            result.stdout.index("| template | templates/HANDOFF.md"),
        )

    def test_require_file_selects_arbitrary_doctrine(self) -> None:
        root = self.make_repo(
            {
                "PROJECT_DOCTRINE.md": """
                    # Project doctrine
                    ## Response rules
                    Preserve the project voice and cite the governing rule.
                """,
                "README.md": "# Project\n\nGeneric overview.\n",
            }
        )
        self.assertEqual(self.build(root).returncode, 0)
        result = self.pack(
            root,
            "prepare a project-specific response",
            "--require-file",
            "PROJECT_DOCTRINE.md",
        )
        self.assertIn("Packet status: PASS", result.stdout)
        self.assertIn("PROJECT_DOCTRINE.md=represented", result.stdout)
        self.assertIn("| required | PROJECT_DOCTRINE.md", result.stdout)

    def test_missing_required_file_produces_fail(self) -> None:
        root = self.make_repo({"README.md": "# Project\n"})
        self.assertEqual(self.build(root).returncode, 0)
        result = self.pack(root, "use doctrine", "--require-file", "MISSING.md")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Packet status: FAIL", result.stdout)
        self.assertIn("MISSING.md=missing", result.stdout)

    def test_unsafe_required_path_is_rejected(self) -> None:
        root = self.make_repo({"README.md": "# Project\n"})
        result = self.pack(root, "use doctrine", "--require-file", "../outside.md")
        self.assertEqual(result.returncode, 3)
        self.assertIn("Packet status: FAIL", result.stdout)
        self.assertIn("unsafe segment", result.stdout)

    def test_required_source_that_cannot_fit_is_not_silently_omitted(self) -> None:
        root = self.make_repo(
            {"PROJECT_DOCTRINE.md": "# Doctrine\n\n" + ("Important doctrine text. " * 100)}
        )
        self.assertEqual(self.build(root).returncode, 0)
        result = self.pack(
            root,
            "use doctrine",
            "--budget",
            "1",
            "--require-file",
            "PROJECT_DOCTRINE.md",
        )
        self.assertIn("Packet status: FAIL", result.stdout)
        self.assertIn("PROJECT_DOCTRINE.md=cannot_fit", result.stdout)
        self.assertIn("required source", result.stdout)

    def test_lower_ranked_candidate_can_fit_after_large_candidates_fail(self) -> None:
        root = self.make_repo(
            {
                "docs/huge-a.md": "# Resume handoff continuation\n\n"
                + ("resume handoff continuation " * 200),
                "docs/huge-b.md": "# Fresh context resume packet\n\n"
                + ("fresh context resume packet " * 200),
                "docs/small.md": "# Resume\n\nSmall useful handoff note.\n",
            }
        )
        self.assertEqual(self.build(root).returncode, 0)
        result = self.pack(root, "resume handoff", "--budget", "30")
        self.assertIn("docs/small.md", result.stdout)
        self.assertIn("docs/huge-a.md", result.stdout)
        self.assertIn("budget", result.stdout)

    def test_parent_and_child_are_not_both_selected(self) -> None:
        root = self.make_repo(
            {
                "HANDOFF.md": """
                    # Handoff
                    Intro.
                    ## Resume packet
                    Continue with one task.
                """
            }
        )
        self.assertEqual(self.build(root).returncode, 0)
        result = self.pack(root, "resume handoff")
        selected_rows = [
            line
            for line in result.stdout.splitlines()
            if line.startswith("| current_state | HANDOFF.md")
        ]
        self.assertEqual(len(selected_rows), 1, result.stdout)

    def test_exact_duplicate_content_is_not_selected_twice(self) -> None:
        duplicate = "# Resume\n\nSame exact handoff guidance.\n"
        root = self.make_repo({"docs/a.md": duplicate, "docs/b.md": duplicate})
        self.assertEqual(self.build(root).returncode, 0)
        result = self.pack(root, "resume handoff")
        excerpts = re.findall(r"^### `docs/[ab]\.md`", result.stdout, flags=re.MULTILINE)
        self.assertEqual(len(excerpts), 1, result.stdout)

    def test_selected_excerpt_renders_complete_reported_range(self) -> None:
        body = "\n".join(f"Line {index}" for index in range(1, 18))
        root = self.make_repo({"HANDOFF.md": f"# Handoff\n\n## Resume packet\n\n{body}\n"})
        self.assertEqual(self.build(root).returncode, 0)
        result = self.pack(root, "resume handoff", "--budget", "300")
        self.assertIn("Line 17", result.stdout)
        self.assertNotIn("\n...\n", result.stdout)
        self.assertRegex(result.stdout, r"HANDOFF\.md \| 3-21")

    def test_embedded_triple_backticks_do_not_break_packet(self) -> None:
        root = self.make_repo(
            {
                "HANDOFF.md": """
                    # Handoff
                    ## Resume packet
                    Use this example:
                    ```python
                    print("safe")
                    ```
                """
            }
        )
        self.assertEqual(self.build(root).returncode, 0)
        result = self.pack(root, "resume handoff")
        self.assertIn("````md", result.stdout)
        self.assertIn('print("safe")', result.stdout)

    def test_table_metadata_escapes_pipes_and_backticks(self) -> None:
        root = self.make_repo(
            {"HANDOFF.md": "# Handoff\n\n## Resume | `packet`\n\nContinue.\n"}
        )
        self.assertEqual(self.build(root).returncode, 0)
        result = self.pack(root, "resume handoff")
        self.assertIn("Resume \\| &#96;packet&#96;", result.stdout)

    def test_non_positive_budgets_fail_clearly(self) -> None:
        root = self.make_repo({"README.md": "# Project\n"})
        for budget in ("0", "-1"):
            result = self.pack(root, "overview", "--budget", budget)
            self.assertEqual(result.returncode, 3)
            self.assertIn("--budget must be a positive integer", result.stdout)

    def test_symlinked_markdown_is_ignored(self) -> None:
        root = self.make_repo({"README.md": "# Project\n"})
        outside = root.parent / f"outside-{root.name}.md"
        outside.write_text("# Outside\n", encoding="utf-8")
        self.addCleanup(lambda: outside.unlink(missing_ok=True))
        os.symlink(outside, root / "LEAK.md")
        result = self.build(root)
        self.assertEqual(result.returncode, 0, result.stderr)
        index_text = (root / ".ai-context/index.jsonl").read_text(encoding="utf-8")
        self.assertNotIn("LEAK.md", index_text)
        self.assertNotIn("Outside", index_text)

    def test_generated_packets_are_not_indexed(self) -> None:
        root = self.make_repo(
            {
                "PACKET.md": """
                    <!-- generated by scripts/context_pack.py -->
                    # Context Packet
                    Generated content.
                """,
                "README.md": "# Project\n",
            }
        )
        self.assertEqual(self.build(root).returncode, 0)
        rows = [
            json.loads(line)
            for line in (root / ".ai-context/index.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        self.assertFalse(any(row["file"] == "PACKET.md" for row in rows))

    def test_packet_fingerprint_is_deterministic(self) -> None:
        root = self.make_repo({"HANDOFF.md": "# Handoff\n\n## Resume packet\n\nContinue.\n"})
        self.assertEqual(self.build(root).returncode, 0)
        first = self.pack(root, "resume handoff")
        second = self.pack(root, "resume handoff")
        first_match = re.search(r"Packet fingerprint: (sha256:[0-9a-f]+)", first.stdout)
        second_match = re.search(r"Packet fingerprint: (sha256:[0-9a-f]+)", second.stdout)
        self.assertIsNotNone(first_match)
        self.assertIsNotNone(second_match)
        self.assertEqual(first_match.group(1), second_match.group(1))

    def test_packet_status_distinguishes_pass_warn_and_fail(self) -> None:
        pass_root = self.make_repo({"HANDOFF.md": "# Handoff\n\n## Resume packet\n\nContinue.\n"})
        self.assertEqual(self.build(pass_root).returncode, 0)
        self.assertIn("Packet status: PASS", self.pack(pass_root, "resume handoff").stdout)

        warn_root = self.make_repo({"HANDOFF.md": "# Handoff\n\n## Resume packet\n\nContinue.\n"})
        self.assertIn("Packet status: WARN", self.pack(warn_root, "resume handoff").stdout)

        fail_root = self.make_repo({"README.md": "# Unrelated\n"})
        self.assertEqual(self.build(fail_root).returncode, 0)
        self.assertIn("Packet status: FAIL", self.pack(fail_root, "unmatched-zebra-task").stdout)

    def test_strict_exit_codes_are_documented_behavior(self) -> None:
        pass_root = self.make_repo({"HANDOFF.md": "# Handoff\n\n## Resume packet\n\nContinue.\n"})
        self.assertEqual(self.build(pass_root).returncode, 0)
        self.assertEqual(self.pack(pass_root, "resume handoff", "--strict").returncode, 0)

        warn_root = self.make_repo({"HANDOFF.md": "# Handoff\n\n## Resume packet\n\nContinue.\n"})
        self.assertEqual(self.pack(warn_root, "resume handoff", "--strict").returncode, 2)

        fail_root = self.make_repo({"README.md": "# Project\n"})
        self.assertEqual(self.build(fail_root).returncode, 0)
        self.assertEqual(
            self.pack(
                fail_root,
                "use doctrine",
                "--require-file",
                "MISSING.md",
                "--strict",
            ).returncode,
            3,
        )

    def test_context_hydration_route_matches_hardening_request(self) -> None:
        root = self.make_repo(
            {
                "docs/context-hydration.md": (
                    "# Context Hydration\n\n## Reliability\n\nHarden packets.\n"
                ),
                "README.md": "# Project\n",
            }
        )
        self.assertEqual(self.build(root).returncode, 0)
        result = self.pack(root, "harden our context hydration packets")
        self.assertIn("Route matches: Context hydration", result.stdout)
        self.assertIn("docs/context-hydration.md", result.stdout)


if __name__ == "__main__":
    unittest.main()
