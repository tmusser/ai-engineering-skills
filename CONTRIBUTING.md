# Contributing

Keep changes small, concrete, and easy to verify. This repository is primarily
Markdown workflow artifacts and standard-library Python tools. Read
[AGENTS.md](AGENTS.md) for repository conventions and the
[documentation index](docs/README.md) to find the relevant guide.

## Make a focused change

1. Describe the failure or friction the change addresses.
2. Edit only the affected guidance or behavior. Keep skills self-contained and
   update related templates or examples when their contract changes.
3. Run the checks below and any focused tests for the behavior you changed.
4. Open a PR explaining the resulting behavior, verification results, and any
   remaining limitations.

Preserve the MIT license and acknowledgments. Do not copy external skill packs
or add performance claims without evidence. A documentation cleanup does not
need a new workflow artifact or a new test that only repeats the wording.

## Local checks

Run from the repository root with Python 3.11 or newer. Markdown linting also
requires Node.js and npm; `npx` downloads the pinned linter if needed.

For every change:

```bash
python -m py_compile scripts/validate_repo.py
python -m py_compile scripts/install_claude_code.py
python scripts/validate_repo.py
npx markdownlint-cli2@0.22.1 "**/*.md"
git diff --check
```

For skill contracts or Python behavior, also run the relevant tests. These
commands cover the broader existing checks without requiring pytest:

```bash
python scripts/check_skill_conformance.py
python -m unittest discover tests
python scripts/run_runnable_examples.py
python scripts/run_negative_examples.py
```

For installer changes, check both targets with `--dry-run` before making an
actual installation. See the [installation guides](docs/README.md#install-and-choose-a-route)
for backup and replacement behavior.

CI definitions in [validate.yml](.github/workflows/validate.yml) and
[ci.yml](.github/workflows/ci.yml) are the source of truth for required checks.
CI also checks Markdown links and exercises the reusable GitHub Action.

## Review expectations

Include the commands you ran and their outcomes in the PR. Distinguish passing
checks from skipped or blocked checks. For a behavior change, explain which
failure the evidence rules out; for docs, check links and copy-paste commands.

Add a concise entry under the existing `Unreleased` section in
[CHANGELOG.md](CHANGELOG.md) when the change affects users. Keep benchmark claims
within the boundaries documented in [LIMITATIONS.md](LIMITATIONS.md).
