# PR Evidence Summary

`scripts/render_pr_evidence.py` turns existing workflow artifacts into a compact
Markdown block for pull request review.

It is a renderer, not a verifier. It can compress evidence that already exists,
run the repository's deterministic verify gate, and check handoff freshness. It
must not reinterpret missing, stale, failing, placeholder, or review-required
state as success.

## Recommended command

Run from the repository root after `SPEC.md` and `VERIFY.md` are current:

```bash
python scripts/render_pr_evidence.py \
  --base origin/main \
  --output /tmp/PR_EVIDENCE.md
```

The command:

- reads `SPEC.md` and `VERIFY.md`;
- runs `scripts/verify_gate.py` against the supplied base;
- checks `HANDOFF.md` with the bundled freshness guard when the file exists;
- writes a review-oriented Markdown summary;
- exits nonzero unless the combined evidence state is `PASS`.

Use `--no-handoff` when continuation state is intentionally outside the pull
request review surface:

```bash
python scripts/render_pr_evidence.py \
  --base origin/main \
  --no-handoff
```

Custom artifact paths are supported:

```bash
python scripts/render_pr_evidence.py \
  --base main \
  --spec artifacts/SPEC.md \
  --verify artifacts/VERIFY.md \
  --handoff artifacts/HANDOFF.md
```

Without `--output`, Markdown is printed to standard output. When an existing
handoff is included, output inside the repository is rejected because creating or
changing that file would invalidate the just-checked handoff snapshot. Write the
summary outside the repository, print it to standard output, or use `--no-handoff`
when continuation state is intentionally excluded.

## Output contract

The renderer produces these sections:

- evidence state;
- objective, acceptance criteria, and explicit non-goals;
- command evidence and remaining uncertainty;
- deterministic and artifact-recorded diff guards;
- unresolved risk;
- continuation state when a handoff is included and fresh.

Example shape:

```markdown
## PR Evidence Summary

### Evidence state
- Overall: **PASS**
- Recorded verify gate: **PASS**
- Deterministic verify gate: **PASS** against `origin/main`
- Handoff freshness: not included

### Objective
- Add a safe export path.

### Verification
- `python -m unittest tests.test_export` — exit `0`; contract tests passed
```

The generated block is intended to be pasted into a pull request description or
review comment. The script does not call GitHub or modify source artifacts.

## Evidence downgrade rules

The combined state is conservative:

- any recorded or deterministic `FAIL` produces `FAIL`;
- a recorded `PASS` without `--base` remains `REVIEW_REQUIRED`;
- missing `SPEC.md`, `VERIFY.md`, statuses, or command evidence remain explicit;
- `_TBD_` and equivalent placeholders are never rendered as evidence;
- a stale or uncheckable handoff blocks continuation output and produces
  `REVIEW_REQUIRED`;
- only recorded `PASS` plus deterministic `PASS`, and fresh included continuation
  state, can produce overall `PASS`.

A missing handoff does not downgrade verification because handoff is optional.
An existing handoff is checked unless `--no-handoff` intentionally excludes it.

## Information boundary

The renderer does not print raw command output. It includes the recorded command,
exit code, interpretation, covered acceptance criterion, and remaining
uncertainty. This keeps the review block compact and reduces the chance of copying
large logs or accidental secrets into a pull request.

The underlying artifacts may still contain sensitive project information. Review
the generated Markdown before posting it outside the repository's normal access
boundary.

## Claim boundary

A `PASS` summary means the supplied artifacts recorded `PASS`, the deterministic
verify gate also returned `PASS`, and any included handoff passed freshness
checking. It does not prove that tests are sufficient, specifications are correct,
or the implementation is defect-free.
