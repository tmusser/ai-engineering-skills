# Changelog

<!-- markdownlint-disable MD013 -->

## [Unreleased]

- Nothing yet.

## [v0.6.0] - TBD

### Added

- Added `docs/bundles.md` with copy-paste starter, bugfix, ML/data science,
  dashboard, agent-worker, and full governance install sets.
- Added root-level `LIMITATIONS.md` with practical edge cases, recovery paths,
  and non-promises.
- Added `docs/agent-worker-safety.md` for scheduled, delegated, or tool-using
  agent-worker pre-flight review.
- Added `docs/release-checklist.md` for maintainer release steps.
- Added a README Common objections section to address prompting, Plan Mode,
  process theater, agent drift, and broader skill-library comparisons.

### Changed

- Made the README starter path visually dominant and copy-pasteable.
- Standardized the starter bundle as exactly `mini-spec`, `scope-freeze`,
  `build-one`, `verify-contract`, and `handoff`.
- Kept `thin-plan` recommended for real repo work, but optional and outside the
  absolute starter path.
- Moved advanced material lower in the README so the first read starts with the
  smallest useful loop.
- Reworked `docs/compatibility-confidence.md` into a matrix that separates
  documented install paths, tested status, confidence, and known caveats.
- Strengthened `ship-mini` guidance for autonomous or scheduled workflows while
  keeping it lightweight.

### Fixed

- Reduced duplicated README language around the starter loop, canonical path,
  proof links, and install examples.
- Softened wording that could imply official vendor support or guaranteed
  automatic skill invocation.
- Clarified that compatibility is documented and locally verifiable, not
  exhaustive across every agent version or client.

### Safety

- Documented default safe stance for agent-worker workflows: read-only by
  default, dry-run before write, narrow data access, no unnecessary secrets,
  human approval for destructive or external side effects, and audit trails for
  autonomous runs.
- Added explicit cautions that these skills reduce risk but do not make
  autonomous agents safe by themselves.
- Added recovery guidance for when `scope-freeze` blocks necessary exploration:
  pause, update the spec/scope explicitly, then resume.

### Compatibility

- Preserved installer hardening:
  - installed skills receive `AI_ENGINEERING_SKILLS_VERSION.json` manifests
  - `--dry-run` remains side-effect free
  - `--backup` preserves replaced or removed installs
  - `--only` supports targeted install/uninstall
  - `--uninstall` removes selected managed skills
  - `--force` is required before overwriting unmanaged or locally modified skill
    folders
  - `--include-templates` is exposed through the shell installer
- Clarified Claude Code, Codex, manual folder copy, and other-agent caveats in
  `docs/compatibility-confidence.md`.

### Migration notes

- Existing users can keep current installs.
- Use `--dry-run` before updating an install path.
- Use `--backup` before replacing or removing managed installs.
- Use `--only` for starter or bundle installs when you do not want every skill.
- Use `--force` only when intentionally replacing unmanaged or locally modified
  skills.
- The v0.6.0 README promotes the five-skill starter path, but no existing skill
  name is removed or renamed.

### Breaking changes

None.

### Validation

Expected local validation before tagging:

```bash
python scripts/validate_repo.py
python -m unittest discover tests
python scripts/run_runnable_examples.py
python scripts/run_negative_examples.py
npx markdownlint-cli2 "**/*.md"
bash install.sh --help
git diff --check
```

CI hardening preserved:

- repo structure validation
- installer behavior tests in fake home/project directories
- runnable examples
- intentionally broken negative examples
- stable installer/help snapshot coverage
- markdown lint and markdown link checks
- Claude/Codex dry-run smoke checks where defined by the workflow

Validation run locally:
- `python scripts/validate_repo.py` — passed
- `python -m unittest discover tests` — 22 tests passed
- `python scripts/run_runnable_examples.py` — runnable example passed
- `python scripts/run_negative_examples.py` — expected failure confirmed
- `npx markdownlint-cli2 "**/*.md"` — 0 errors
- `bash install.sh --help` — displayed usage
- `git diff --check` — clean
