# Release Checklist

<!-- markdownlint-disable MD013 -->

Use this checklist before tagging a release. It is for maintainers; it does not mean
that the release has already been published.

## Required local validation

Run:

```bash
python scripts/validate_repo.py
python -m unittest discover tests
python scripts/run_runnable_examples.py
python scripts/run_negative_examples.py
npx markdownlint-cli2 "**/*.md"
bash install.sh --help
git diff --check
```

Confirm any CI-required checks in `.github/workflows/validate.yml` still match the
claims in README, CHANGELOG, and docs.

## Documentation checks

- README starter path is clear and copy-pasteable.
- Starter means exactly:
  - `mini-spec`
  - `scope-freeze`
  - `build-one`
  - `verify-contract`
  - `handoff`
- `thin-plan` is optional/recommended, not part of the absolute starter set.
- `LIMITATIONS.md` exists and is linked from the README.
- `docs/bundles.md` exists and uses valid skill names.
- `docs/agent-worker-safety.md` aligns with `skills/ship-mini/SKILL.md`.
- `docs/compatibility-confidence.md` avoids vendor-support claims.
- Install command examples are accurate.
- Internal links pass markdown link checking.

## Changelog checks

- `CHANGELOG.md` has `## [Unreleased]`.
- Target release section is present, for example `## [v0.6.0] - TBD` before the
  date is known.
- Breaking changes are explicit, even when the answer is `None`.
- Migration notes explain `--dry-run`, `--backup`, `--only`, and `--force`.
- Validation commands or CI checks are listed factually.

## Safety checks

- Autonomous or scheduled workflow language says safety is bounded and still
  requires human judgment.
- No doc claims the repo makes autonomous agents safe by itself.
- Destructive operations, secrets, broad data access, external side effects,
  rollback, owner notification, and stop conditions are covered in the safety docs
  or `ship-mini`.

## Compatibility checks

- Claude Code and Codex are described as documented install paths, not official
  vendor-supported integrations.
- Manual install is presented as a fallback that depends on the receiving agent.
- Other agents are best-effort unless locally verified.

## Publish steps

After merge and validation:

1. Replace `TBD` in `CHANGELOG.md` with the release date.
2. Commit the changelog date update.
3. Tag the release.
4. Push the tag.
5. Create GitHub Release notes from `CHANGELOG.md`.
6. Include breaking changes and migration notes.
7. Include validation commands run.
8. Verify the README starter commands still copy cleanly from GitHub.
