# Case Study: Cursor CLI Delegation for `tmusser/skill-codex`

## Goal

Use `ai-engineering-skills` to guide a real external OSS contribution that extended `tmusser/skill-codex` with Cursor-side delegation paths, while keeping the external repo unchanged from here.

## Context

The target repo already handled Codex workflows and Cursor-as-host packaging. The new work added a Cursor-as-worker path so other agents could delegate bounded implementation and review tasks to Cursor CLI.

## Problem

The contribution needed to separate host and worker roles, confirm the installed Cursor CLI shape before using it, and keep the delegation packets small enough that the external repo stayed readable and safe to maintain.

## Workflow used

1. `grill-with-docs-lite` to check the repo language, existing roles, and missing boundary details.
2. `mini-spec` to define the contribution as a small, verifiable slice.
3. `thin-plan` to split the work into Cursor-host, Cursor-worker, and hardening slices.
4. `scope-freeze` to keep each slice narrow and avoid accidental expansion.
5. `build-one` to implement one slice at a time in the external repo.
6. `test-mini` to verify README guidance, skill prompts, and CLI-shape assumptions.
7. `verify-contract` to record branch state, commit evidence, and remaining risk.
8. `handoff` to preserve what changed and what still needed judgment.

## What changed externally

- Added Cursor-adapted host-side skills for Codex workflows.
- Added `skills/cursor_exec` and `skills/cursor_review` so Claude Code, Codex, or another host could delegate bounded work to Cursor CLI.
- Hardened the guidance around `--help` detection, working-directory handling, no-auto-commit defaults, and fallback behavior.

## What stayed out of the external repo

- No changes to this repo's skills or installers.
- No attempt to turn the external repo into a general agent framework.
- No broad redesign of the existing Codex workflows.

## Verification

- The local branch state showed `cursor-cli-delegation...origin/cursor-cli-delegation [ahead 1]` while the hardening work was in progress.
- Commit `849c22a` tightened the delegation docs and skills in the external repo.
- The external repo README and skill files confirmed the host/worker split, CLI `--help` checks, bounded prompts, and no-auto-commit defaults.

## Lessons

- A small spec plus narrow slices works just as well for external OSS contributions as it does for local features.
- The most useful boundary work was not the code itself; it was the prompt and README structure that made the Cursor delegation behavior hard to misuse.
- The same workflow can produce code and documentation without turning either into a sprawling process artifact.

## Reusable pattern

When contributing to another repo, use the same loop: clarify the target repo's language, freeze each slice, keep verification explicit, and leave a handoff record here instead of depending on the target repo's history.
