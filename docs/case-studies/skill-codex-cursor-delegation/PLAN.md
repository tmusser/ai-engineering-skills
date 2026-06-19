# PLAN

## Implementation slices

1. Write the case study README with context, workflow, results, and lessons.
2. Capture the supporting `SPEC.md`, `PLAN.md`, `VERIFY.md`, and `HANDOFF.md` artifacts in the same folder.
3. Add a small link to the case study from the main README.
4. Add a discoverability link in `docs/SUITE_MAP.md` if it keeps the proof easy to find.
5. Validate the repo and inspect the diff.

## Dependencies

- Existing case study style in `docs/case-study-context-to-action-skills.md`.
- Branch and commit evidence from the external `skill-codex` repo.

## Risk notes

- Do not imply that this repo modified the external repo.
- Do not overstate verification beyond the evidence captured locally.
- Keep the writeup short enough that it reads like a proof artifact, not a blog post.

## Verification strategy

- Check markdown rendering by inspection.
- Run the repo validator.
- Confirm the new links point to the new case study folder.
