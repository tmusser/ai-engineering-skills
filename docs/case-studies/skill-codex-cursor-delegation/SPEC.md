# SPEC

## Goal

Capture a concise case study showing how `ai-engineering-skills` guided a real external OSS contribution to `tmusser/skill-codex` on branch `cursor-cli-delegation`.

## User / use case

A builder wants a short proof that the workflow helps on a neighboring repo without bloating the target repo or turning the story into a generic process essay.

## Acceptance criteria

- The case study stays factual and compact.
- It names the workflow used.
- It captures what changed externally and what stayed out.
- It links from the main README and is easy to find from the suite map.
- It records verification evidence and remaining decisions.

## Non-goals

- No edits to `tmusser/skill-codex` from this repo.
- No replay of the full external branch history.
- No broad rewrite of the main README.

## Constraints

- Use only evidence already observed in local inspection.
- Keep the artifacts short and copy/paste-friendly.
- Preserve the repo's technical-builder positioning.

## Verification

- Case study folder contains `README.md`, `SPEC.md`, `PLAN.md`, `VERIFY.md`, and `HANDOFF.md`.
- `README.md` links to the case study.
- `python scripts/validate_repo.py` passes.
