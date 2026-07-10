# Changelog

<!-- markdownlint-disable MD013 -->

## [Unreleased]

### Added

- Added an optional `ceremony-budget` pre-flight skill that routes tasks to the
  smallest workflow that still buys back enough attention and safety.
- Added [docs/ceremony-budget.md](docs/ceremony-budget.md) to explain why
  ceremony budget exists, how Level 0-3 routing works, and when to escalate or
  de-escalate.
- Added a fast routing test that selects the first ceremony level leaving no named
  risk uncovered.

### Changed

- Updated the README, workflow recipes, skill map, and bundles docs to position
  `ceremony-budget` as an optional router before the existing ceremony ladder.
- Clarified that bundles control installed capabilities while `ceremony-budget`
  controls which skills a task actually needs.
- Aligned `LLM.md` and the skill map with the five-skill durable starter loop,
  optional focused testing, and continuation-only handoffs.

### Fixed

- Removed conflicting agent-facing guidance that treated the starter bundle as the
  minimum runtime process for every task.

## [v0.7.0] - 2026-07-03

### Added

- Added a root `LLM.md` guide for agent-facing repo navigation and workflow
  expectations.
- Added a worktree agent-run recipe in `docs/worktree-agent-run.md` and linked it
  from the docs and README recipe indexes.
- Added a README compatibility matrix, a faster try-it path, and a short
  "What you can do" routing table.
- Added a lightweight secret-boundary checklist and structured command evidence
  guidance to verification artifacts.
- Added an optional context hydration recipe with a local markdown indexer,
  packet generator, and routing map.
- Added optional subagent / small-model routing guidance and a reusable
  context-librarian prompt template for the context hydration recipe.
- Added explicit `--refresh-index` freshness handling and selected-context
  budget guardrails to the context hydration tooling.

### Changed

- Reframed the README hero around `ai-engineering-skills` as the control layer
  for coding agents.
- Added a short README section explaining how this repo complements sandboxing
  and observability tools.

### Migration notes

- This release adds optional context hydration tooling for advanced local workflows.
- Existing skill behavior and starter usage are unchanged; context hydration is
  optional tooling and documentation for advanced local workflows.
- Verification entries now expect concise command-level evidence and may use
  `REVIEW_REQUIRED` if credential exposure is uncertain.

## [v0.6.1] - 2026-06-26

### Added

- Added `scripts/verify_gate.py`, a deterministic evidence checker for
  `SPEC.md`, `VERIFY.md`, and the current git diff.
- Added text and JSON verify-gate output.
- Added conservative diff guards for tests, fixtures/data, dependencies,
  protected paths, and forbidden paths.
- Added `PASS`, `FAIL`, and `REVIEW_REQUIRED` gate semantics to the
  verification workflow.
- Added `docs/loop-governance.md` for bounded agent iteration.
- Added a Data Trust Pass recipe for metric, denominator, leakage, and
  claim-boundary checks.

### Changed

- Refactored the README into a sharper front door and moved deeper explanation
  into docs.
- Clarified the repo as a state layer for explicit, inspectable, recoverable,
  and gateable agent work.
- Updated workflow artifacts around compatibility seams, invalid-if
  constraints, test integrity, durable build notes, and verification
  guardrails.
- Added optional loop-contract, loop-readiness, and loop-state fields to
  `SPEC.md`, `VERIFY.md`, and `HANDOFF.md`.
- Updated docs to emphasize auditability, verification discipline, and
  resumability instead of broad skill superiority.

### Fixed

- Limited root `pytest` discovery to the intended `tests/` suite.
- Removed stale/duplicate docs naming around `why-skills-not-prompts`.
- Tightened validation so new gate scripts, docs, and tests are covered.
- Made verify-gate diff checks working-tree-aware, including staged, unstaged,
  untracked, and deleted files.

### Claim boundary

Current evidence supports auditability, verification discipline, and
resumability claims. It does not prove broad pass-rate superiority over strong
prompting or strong models.

## [v0.6.0] - 2026-06-21

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
