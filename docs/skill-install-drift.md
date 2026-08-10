# Installed Skill Drift

`scripts/check_skill_install.py` compares installed Claude Code or Codex skills against both their recorded install snapshot and the current repository copy.

The checker is read-only. It does not reinstall skills, overwrite local customizations, add hooks, run at agent startup, or create background monitoring.

## Why this works without a new manifest format

The existing installers already write `AI_ENGINEERING_SKILLS_VERSION.json` inside each managed skill directory. That manifest records:

- package and skill identity;
- installer target;
- source repository commit;
- install timestamp;
- SHA-256 content hash for the installed skill tree.

That gives the checker three useful states to compare:

1. current repository skill content;
2. current installed skill content;
3. content hash recorded when the skill was installed.

No second provenance ledger is required.

## Usage

Check the user-level Claude Code install:

```bash
python scripts/check_skill_install.py --target claude
```

Check Codex through the unified CLI:

```bash
python scripts/aes.py drift --target codex
```

Check only selected skills:

```bash
python scripts/aes.py drift \
  --target claude \
  --only mini-spec,scope-freeze,build-one
```

Check a project-local install:

```bash
python scripts/aes.py drift \
  --target codex \
  --project-path /path/to/project
```

Machine-readable output:

```bash
python scripts/aes.py drift --target claude --format json
```

## Per-skill states

### `CURRENT`

The installed files still match their recorded install snapshot, and that snapshot matches the current repository skill.

### `OUTDATED`

The installed files still match their recorded install snapshot, but the current repository skill has changed since that snapshot.

This state is safe to repair with the normal installer because no local modification was detected.

### `LOCALLY_MODIFIED`

The installed files differ from the content hash recorded when they were installed.

Local modifications take precedence over repository drift. The checker does not recommend `--force` automatically because doing so would destroy the local state it just detected.

### `MISSING`

The selected skill is not installed at the checked target.

This state is safe to repair with the normal installer.

### `REVIEW_REQUIRED`

The checker cannot establish a trustworthy baseline. Examples include:

- a skill directory without an AI Engineering Skills manifest;
- an invalid or incomplete manifest;
- a manifest that says the skill was installed for a different target.

The checker does not guess that these states are either current or locally modified.

## Overall status and exits

The command reports one overall state:

- `CURRENT`: every selected skill is current; exit `0`;
- `DRIFT`: at least one selected skill is missing, outdated, or locally modified, with no untrusted manifest state; exit `1`;
- `REVIEW_REQUIRED`: at least one selected skill lacks trustworthy provenance; exit `2`.

`LOCALLY_MODIFIED` is drift, but not automatically repairable drift.

## Repair behavior

When only `MISSING` or `OUTDATED` skills need repair, the checker prints the exact existing installer command, for example:

```bash
python scripts/aes.py install --claude-user --only mini-spec,scope-freeze
```

For project-local installs it uses the corresponding `--claude-project` or `--codex-project` form.

The repair command deliberately excludes `LOCALLY_MODIFIED` and `REVIEW_REQUIRED` skills. Those require a human decision before replacement.

## Boundaries

This checker does not:

- modify installed files;
- invoke the installer;
- suggest destructive `--force` replacement for local edits;
- check templates or arbitrary agent configuration;
- prove that an installed skill is behaviorally correct;
- register a Git hook or agent lifecycle hook;
- run automatically at startup or in the background.

It answers one narrow question: whether installed skill files still correspond to a trusted installation snapshot and the current repository copy.
