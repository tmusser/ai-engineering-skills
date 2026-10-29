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
- prefers valid schema-v1 structured verification evidence when present, with legacy command-evidence parsing only when the structured section is absent;
- runs `scripts/verify_gate.py` against the supplied base, including opt-in compatibility probe matching, verification freshness, and stable REVIEW_REQUIRED reason codes when those contracts are present;
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

## Optional acceptance-to-evidence coverage

Tag every acceptance criterion with a stable ID to opt into coverage checks:

```markdown
## Acceptance criteria

- AC-1: CSV export preserves the original columns.
- AC-2: Zero matches produce a header-only CSV.
```

In schema-v1 structured verification evidence, record the single matching ID
in each check's `acceptance_criterion` field. Each check links to one ID; use
separate checks for independently verified criteria.

```json
{
  "check": "empty-result-test",
  "command": "python -m pytest tests/test_export.py",
  "exit_code": 0,
  "evidence_source": "command",
  "status": "PASS",
  "evidence": "Header-only output observed",
  "recorded_at": "2026-10-27T12:00:00Z",
  "acceptance_criterion": "AC-2"
}
```

When IDs are present, the PR renderer shows a criterion/check/coverage table.
A missing link, duplicate ID, mixed numbered and unnumbered criteria, invalid
structured evidence, inferred-only evidence, or an unknown ID downgrades its
summary to `REVIEW_REQUIRED`. Explicit linked `FAIL` stays FAIL.
Legacy unnumbered specs are unchanged, including their exit codes.

The same deterministic coverage check is available independently:

```bash
python scripts/acceptance_coverage.py --spec SPEC.md --verify VERIFY.md
python scripts/acceptance_coverage.py --format json
```

Exit codes: `0` = PASS / NOT_APPLICABLE, `3` = REVIEW_REQUIRED,
`1` = FAIL, `2` = unreadable inputs. The standalone command does not
execute tests or invoke the Git diff-aware verification gate.

**Claim boundary:** LINKED means valid recorded evidence *claims* coverage.
It does not prove the test ran, its assertions were correct, the right behavior
was specified, or its result remains fresh. Existing verification/freshness gates
retain those responsibilities. No extra mandatory stage or second evidence
schema is introduced.

## Output contract

The renderer produces these sections:

- evidence state, including deterministic review reason codes when present;
- objective, acceptance criteria, and explicit non-goals;
- optional acceptance-to-evidence matrix for SPEC criteria tagged with `AC-*` IDs;
- structured verification checks (or legacy command evidence) and remaining uncertainty;
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
- **unit-tests** [command] — PASS; `python -m unittest tests.test_export` exit `0`; 4 tests passed
  - Provenance: recorded 2026-10-06T10:00:00Z, commit abc123
```

The generated block is intended to be pasted into a pull request description or
review comment. The script does not call GitHub or modify source artifacts.

## Evidence downgrade rules

The combined state is conservative:

- any recorded or deterministic `FAIL` produces `FAIL`;
- explicit criterion IDs activate coverage; unlinked criteria require review, and linked failing checks prevent PASS;
- a recorded `PASS` without `--base` remains `REVIEW_REQUIRED`;
- missing `SPEC.md`, `VERIFY.md`, statuses, or command evidence remain explicit;
- `_TBD_` and equivalent placeholders are never rendered as evidence;
- once structured verification evidence exists, malformed JSON, invalid schema fields, duplicate check IDs, contradictory PASS command exit codes, or missing provenance produce `REVIEW_REQUIRED`; an explicit structured `FAIL` produces `FAIL`;
- invalid structured evidence is not silently replaced by legacy prose evidence;
- required compatibility probes with missing, mismatched, or review-required post-change evidence produce `REVIEW_REQUIRED`, while an explicit failed post-change probe produces `FAIL`;
- stamped verification whose repository fingerprint no longer matches is stale and produces `REVIEW_REQUIRED` with a stable reason code;
- a stale or uncheckable handoff blocks continuation output and produces
  `REVIEW_REQUIRED`;
- only recorded `PASS` plus deterministic `PASS`, and fresh included continuation
  state, can produce overall `PASS`.

When the deterministic verify gate requires review, the renderer surfaces its stable reason codes (for example `VERIFICATION_STALE`, `TESTS_CHANGED`, or `DIFF_BUDGET_EXCEEDED`) while retaining the original prose reason. See [REVIEW_REQUIRED reason taxonomy](review-required-taxonomy.md).

A missing handoff does not downgrade verification because handoff is optional.
An existing handoff is checked unless `--no-handoff` intentionally excludes it.

## Information boundary

The renderer does not print raw command output. For structured evidence it includes the check ID, evidence source, status, command/exit code when present, concise evidence, provenance, covered acceptance criterion, and remaining uncertainty. For legacy artifacts it keeps the older command-evidence rendering. This keeps the review block compact and reduces the chance of copying
large logs or accidental secrets into a pull request.

The underlying artifacts may still contain sensitive project information. Review
the generated Markdown before posting it outside the repository's normal access
boundary.

## Claim boundary

A `PASS` summary means the supplied artifacts recorded `PASS`, the deterministic
verify gate also returned `PASS`, and any included handoff passed freshness
checking. It does not prove that tests are sufficient, specifications are correct,
or the implementation is defect-free.
