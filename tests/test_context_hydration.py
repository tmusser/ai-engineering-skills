from __future__ import annotations

import json
import os
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


def run_script(script: Path, *args: str, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, str(script), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def route_file_text(max_selected_context_tokens: int = 1500) -> str:
    return """
    max_selected_context_tokens: {max_selected_context_tokens}
    routes:
      resume_handoff:
        label: Resume / handoff
        keywords: handoff, resume, fresh context, resume packet, continuation
        files: templates/HANDOFF.md, skills/handoff/SKILL.md, docs/recipes.md

      verification:
        label: Verification
        keywords: verify, verification, evidence, review required, review_required
        files: templates/VERIFY.md, skills/verify-contract/SKILL.md, skills/test-mini/SKILL.md

      scope_control:
        label: Scope control
        keywords: scope, boundary, freeze, blast radius, unrelated edits
        files: skills/scope-freeze/SKILL.md, docs/recipes.md, docs/skill-map.md

      planning:
        label: Planning
        keywords: plan, spec, checklist, mini-spec, thin-plan
        files: skills/mini-spec/SKILL.md, skills/checklist-mini/SKILL.md, skills/thin-plan/SKILL.md, templates/SPEC.md, templates/PLAN.md

      debugging:
        label: Debugging
        keywords: debug, bug, diagnose, failure, regression, loop
        files: skills/diagnose-loop/SKILL.md, skills/bug-capture/SKILL.md, docs/recipes.md

      shipping:
        label: Shipping
        keywords: ship, release, deploy, publish, rollout
        files: skills/ship-mini/SKILL.md, docs/release-checklist.md, docs/agent-worker-safety.md
    """.format(max_selected_context_tokens=max_selected_context_tokens)


def skill_doc(title: str, extra_heading: str, body: str) -> str:
    return f"""
    ---
    name: {title.lower().replace(' ', '-')}
    description: {body}
    ---

    # {title}

    ## Purpose

    {body}

    ## {extra_heading}

    {body}
    """


class ContextHydrationTests(unittest.TestCase):
    maxDiff = None

    def make_repo(self, files: dict[str, str]) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        tempdir = tempfile.TemporaryDirectory()
        root = Path(tempdir.name)
        for relative_path, text in files.items():
            write_text(root / relative_path, text)
        self.addCleanup(tempdir.cleanup)
        return tempdir, root

    def run_build(self, root: Path) -> subprocess.CompletedProcess[str]:
        return run_script(BUILD_SCRIPT, "--root", str(root), cwd=root)

    def run_pack(self, root: Path, task: str, *extra: str) -> subprocess.CompletedProcess[str]:
        return run_script(PACK_SCRIPT, "--root", str(root), task, *extra, cwd=root)

    def test_build_context_index_is_stable_and_ignores_code_fences(self) -> None:
        _, root = self.make_repo(
            {
                "README.md": """
                    # Project

                    Intro text.

                    ## Start Here

                    Alpha.

                    ```md
                    # Ignored heading
                    ```

                    ### Details

                    Beta.

                    ## Wrap Up

                    Gamma.
                """,
                "docs/sample.md": """
                    Title
                    =====

                    Body text.

                    Another section
                    ---------------

                    More text.
                """,
            }
        )

        first = self.run_build(root)
        self.assertEqual(first.returncode, 0, first.stderr)
        index_path = root / ".ai-context" / "index.jsonl"
        self.assertTrue(index_path.is_file())
        first_bytes = index_path.read_text(encoding="utf-8")

        second = self.run_build(root)
        self.assertEqual(second.returncode, 0, second.stderr)
        second_bytes = index_path.read_text(encoding="utf-8")
        self.assertEqual(first_bytes, second_bytes)

        rows = [json.loads(line) for line in first_bytes.splitlines() if line.strip()]
        self.assertEqual(len(rows), 6)
        self.assertEqual(
            set(rows[0].keys()),
            {
                "approx_token_estimate",
                "content_hash",
                "end_line",
                "file",
                "heading_level",
                "heading_path",
                "start_line",
            },
        )
        self.assertTrue(rows[0]["content_hash"].startswith("sha256:"))
        self.assertFalse(any("Ignored heading" in json.dumps(row) for row in rows))

    def test_build_context_index_keeps_duplicate_heading_paths_distinct(self) -> None:
        _, root = self.make_repo(
            {
                "docs/dup-headings.md": """
                    # Root

                    ## Alpha

                    ### Shared

                    Alpha text.

                    ## Beta

                    ### Shared

                    Beta text.
                """,
            }
        )

        result = self.run_build(root)
        self.assertEqual(result.returncode, 0, result.stderr)
        rows = [
            json.loads(line)
            for line in (root / ".ai-context" / "index.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        shared_paths = [tuple(row["heading_path"]) for row in rows if row["heading_path"] and row["heading_path"][-1] == "Shared"]
        self.assertEqual(shared_paths, [("Root", "Alpha", "Shared"), ("Root", "Beta", "Shared")])

    def test_context_pack_routes_common_task_terms(self) -> None:
        _, root = self.make_repo(
            {
                ".ai-context/routing.yml": route_file_text(),
                "templates/HANDOFF.md": """
                    # Handoff

                    ## Resume packet

                    Continue later.
                """,
                "templates/VERIFY.md": """
                    # Verify

                    ## Verify gate

                    Status: PASS
                """,
                "templates/SPEC.md": """
                    # Spec

                    ## Objective

                    Scope this slice.
                """,
                "templates/PLAN.md": """
                    # Plan

                    ## Implementation slices

                    One small slice.
                """,
                "docs/release-checklist.md": """
                    # Release Checklist

                    ## Compatibility checks

                    Keep it factual.
                """,
                "docs/agent-worker-safety.md": """
                    # Agent Worker Safety

                    ## When to use

                    Use carefully.
                """,
                "skills/handoff/SKILL.md": skill_doc("Handoff", "Workflow", "Preserve state."),
                "skills/verify-contract/SKILL.md": skill_doc("Verify Contract", "Workflow", "Record evidence."),
                "skills/test-mini/SKILL.md": skill_doc("Test Mini", "Workflow", "Run focused tests."),
                "skills/scope-freeze/SKILL.md": skill_doc("Scope Freeze", "Workflow", "Keep edits bounded."),
                "skills/mini-spec/SKILL.md": skill_doc("Mini Spec", "Workflow", "Define the slice."),
                "skills/checklist-mini/SKILL.md": skill_doc("Checklist Mini", "Workflow", "List readiness checks."),
                "skills/thin-plan/SKILL.md": skill_doc("Thin Plan", "Workflow", "Split into slices."),
                "skills/diagnose-loop/SKILL.md": skill_doc("Diagnose Loop", "Workflow", "Break repeated loops."),
                "skills/bug-capture/SKILL.md": skill_doc("Bug Capture", "Workflow", "Write a repro."),
                "skills/ship-mini/SKILL.md": skill_doc("Ship Mini", "Workflow", "Record release checks."),
            }
        )

        build = self.run_build(root)
        self.assertEqual(build.returncode, 0, build.stderr)

        result = self.run_pack(
            root,
            "resume handoff verify scope plan debug ship",
            "--budget",
            "5000",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        stdout = result.stdout
        self.assertIn("Route matches:", stdout)
        for label in (
            "Resume / handoff",
            "Verification",
            "Scope control",
            "Planning",
            "Debugging",
            "Shipping",
        ):
            self.assertIn(label, stdout)
        self.assertTrue(
            any(name in stdout for name in ("templates/HANDOFF.md", "skills/handoff/SKILL.md")),
            stdout,
        )
        self.assertTrue(
            any(
                name in stdout
                for name in ("templates/VERIFY.md", "skills/verify-contract/SKILL.md")
            ),
            stdout,
        )
        self.assertIn("skills/scope-freeze/SKILL.md", stdout)
        self.assertTrue(
            any(name in stdout for name in ("templates/SPEC.md", "skills/thin-plan/SKILL.md")),
            stdout,
        )
        self.assertIn("skills/diagnose-loop/SKILL.md", stdout)
        self.assertIn("skills/ship-mini/SKILL.md", stdout)
        self.assertIn("## Omitted candidates", stdout)
        self.assertIn("## Refresh guidance", stdout)

    def test_context_pack_handles_budget_one_without_crashing(self) -> None:
        _, root = self.make_repo(
            {
                ".ai-context/routing.yml": route_file_text(),
                "templates/HANDOFF.md": """
                    # Handoff

                    ## Resume packet

                    Continue later with the same task context and no extra detours.
                """,
                "skills/handoff/SKILL.md": skill_doc("Handoff", "Workflow", "Preserve state."),
            }
        )

        build = self.run_build(root)
        self.assertEqual(build.returncode, 0, build.stderr)

        result = self.run_pack(root, "handoff", "--budget", "1")
        self.assertEqual(result.returncode, 0, result.stderr)
        stdout = result.stdout
        self.assertIn("Route matches: Resume / handoff", stdout)
        self.assertIn("## Selected context", stdout)
        self.assertIn("- No records selected.", stdout)
        self.assertIn(
            "No records fit within the packet budget. Increase `--budget` or inspect the omitted candidates directly.",
            stdout,
        )
        self.assertIn("## Omitted candidates", stdout)
        self.assertIn("exceeds budget", stdout)
        self.assertIn("## Refresh guidance", stdout)

    def test_context_pack_renders_omitted_candidates_without_preferred_files(self) -> None:
        _, root = self.make_repo(
            {
                ".ai-context/routing.yml": route_file_text(),
                "docs/handoff-alpha.md": """
                    # Handoff Alpha

                    ## Resume packet

                    Keep this session focused on the current slice, the current evidence,
                    and the current handoff notes.
                """,
                "docs/handoff-beta.md": """
                    # Handoff Beta

                    ## Resume packet

                    Keep this session focused on the current slice, the current evidence,
                    the current handoff notes, and the next verification step.
                """,
            }
        )

        build = self.run_build(root)
        self.assertEqual(build.returncode, 0, build.stderr)

        result = self.run_pack(root, "handoff", "--budget", "30")
        self.assertEqual(result.returncode, 0, result.stderr)
        stdout = result.stdout
        self.assertIn("Route matches: Resume / handoff", stdout)
        self.assertIn("docs/handoff-alpha.md", stdout)
        self.assertIn("docs/handoff-beta.md", stdout)
        self.assertIn("## Omitted candidates", stdout)
        self.assertNotIn("## Omitted candidates\n\n- None.", stdout)

    def test_context_pack_warns_when_index_is_older_than_markdown(self) -> None:
        _, root = self.make_repo(
            {
                ".ai-context/routing.yml": route_file_text(),
                "templates/HANDOFF.md": """
                    # Handoff

                    ## Resume packet

                    Continue later.
                """,
                "skills/handoff/SKILL.md": skill_doc("Handoff", "Workflow", "Preserve state."),
            }
        )

        build = self.run_build(root)
        self.assertEqual(build.returncode, 0, build.stderr)
        index_path = root / ".ai-context" / "index.jsonl"
        index_mtime_ns = index_path.stat().st_mtime_ns

        markdown_path = root / "templates" / "HANDOFF.md"
        os.utime(
            markdown_path,
            ns=(index_mtime_ns + 5_000_000, index_mtime_ns + 5_000_000),
        )

        result = self.run_pack(root, "handoff")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("## Index freshness", result.stdout)
        self.assertIn("index older than markdown files", result.stdout)

    def test_context_pack_refresh_index_before_packet_generation(self) -> None:
        _, root = self.make_repo(
            {
                ".ai-context/routing.yml": route_file_text(),
                "templates/HANDOFF.md": """
                    # Handoff

                    ## Resume packet

                    Continue later.
                """,
                "skills/handoff/SKILL.md": skill_doc("Handoff", "Workflow", "Preserve state."),
            }
        )

        build = self.run_build(root)
        self.assertEqual(build.returncode, 0, build.stderr)
        index_path = root / ".ai-context" / "index.jsonl"
        before_index_text = index_path.read_text(encoding="utf-8")

        write_text(
            root / "templates" / "HANDOFF.md",
            """
            # Handoff

            ## Resume packet

            Continue later with refreshed index content.
            """,
        )

        result = self.run_pack(root, "handoff", "--refresh-index")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("index refreshed before packet generation", result.stdout)
        self.assertNotIn("index older than markdown files", result.stdout)
        self.assertNotIn("stale content hash", result.stdout)
        after_index_text = index_path.read_text(encoding="utf-8")
        self.assertNotEqual(before_index_text, after_index_text)

    def test_context_pack_clamps_budget_to_route_max(self) -> None:
        _, root = self.make_repo(
            {
                ".ai-context/routing.yml": route_file_text(max_selected_context_tokens=40),
                "templates/HANDOFF.md": """
                    # Handoff

                    ## Resume packet

                    Continue later.
                """,
                "skills/handoff/SKILL.md": skill_doc("Handoff", "Workflow", "Preserve state."),
            }
        )

        build = self.run_build(root)
        self.assertEqual(build.returncode, 0, build.stderr)

        result = self.run_pack(root, "handoff", "--budget", "5000")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("requested budget 5000 exceeds max 40; clamped to 40", result.stdout)
        self.assertIn("Selected-context budget: approximately 40 tokens", result.stdout)

    def test_context_pack_reports_stale_index_when_source_changes(self) -> None:
        _, root = self.make_repo(
            {
                ".ai-context/routing.yml": route_file_text(),
                "templates/HANDOFF.md": """
                    # Handoff

                    ## Resume packet

                    Continue later.
                """,
                "templates/VERIFY.md": """
                    # Verify

                    ## Verify gate

                    Status: PASS
                """,
                "skills/handoff/SKILL.md": skill_doc("Handoff", "Workflow", "Preserve state."),
                "skills/verify-contract/SKILL.md": skill_doc("Verify Contract", "Workflow", "Record evidence."),
            }
        )

        build = self.run_build(root)
        self.assertEqual(build.returncode, 0, build.stderr)

        write_text(
            root / "templates" / "VERIFY.md",
            """
            # Verify

            ## Verify gate

            Status: FAIL
            """,
        )

        result = self.run_pack(root, "verify handoff")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Stale-index warnings", result.stdout)
        self.assertTrue(
            "stale content hash" in result.stdout or "missing index entry" in result.stdout,
            result.stdout,
        )

    def test_context_pack_reports_missing_index_without_spam(self) -> None:
        _, root = self.make_repo(
            {
                ".ai-context/routing.yml": route_file_text(),
                "templates/HANDOFF.md": """
                    # Handoff

                    ## Resume packet

                    Continue later.
                """,
            }
        )

        result = self.run_pack(root, "handoff")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("index missing:", result.stdout)
        self.assertNotIn("missing index entry for current markdown", result.stdout)


if __name__ == "__main__":
    unittest.main()
