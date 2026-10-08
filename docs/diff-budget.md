# Implementation Diff Budget

An implementation diff budget is an optional review tripwire for changes that are
supposed to stay small.

It complements, rather than replaces, the existing scope gate:

- `scope-freeze` owns the hard write boundary. Exceeding its declared
  `Max files changed` is a scope `FAIL`.
- the SPEC implementation diff budget owns expected patch size. Exceeding it is
  `REVIEW_REQUIRED`, because a larger patch may be legitimate but should not
  silently inherit a small-task trust posture.

## Declare a budget

Add this optional section to `SPEC.md`:

```text
## Implementation diff budget

Diff budget requirement: ENFORCED

- Max changed files: 3
- Max added lines: 120
```

Use:

```text
Diff budget requirement: NOT_APPLICABLE
```

when no meaningful numeric implementation-size expectation exists.

Do not invent arbitrary limits for ceremony. An enforced budget should come from
an accepted narrow slice, explicit user constraint, or other defensible scope
expectation before implementation expands.

## Deterministic check

Run the normal verify gate:

```bash
python scripts/verify_gate.py --base origin/main
```

When an enforced budget exists, the output includes a `Diff-budget` check such
as:

```text
Diff-budget: PASS - implementation diff: 2/3 changed files, 47/120 added lines
```

or:

```text
Diff-budget: REVIEW_REQUIRED - implementation diff: 5/3 changed files, 164/120 added lines; budget exceeded: changed files 5 > 3, added lines 164 > 120
```

A budget overrun prevents overall `PASS` until the expansion is reviewed. It
does not automatically convert otherwise-correct behavior into `FAIL`.

## What counts

The gate counts implementation changes against the supplied Git base.

Changed-file count includes tracked, staged, unstaged, and untracked
implementation files.

Added-line count includes:

- tracked/staged/unstaged text additions from Git numstat;
- all text lines in new untracked files.

Binary or otherwise unmeasurable changed files make an enforced added-line budget
`REVIEW_REQUIRED` because the line count cannot be established safely.

Rename-heavy changes are intentionally conservative: the line budget uses a
no-renames numstat view, so moved content may be counted as additions. Treat that
review signal as a reason to inspect the patch rather than as proof of excessive
new logic.

## Workflow artifacts do not consume the budget

Common control artifacts are excluded from the implementation budget, including:

- `SPEC.md`
- `SCOPE.md`
- `VERIFY.md`
- `HANDOFF.md`
- `PLAN.md`
- `TODO.md`
- `ANALYZE.md`
- `BUGS.md`
- `DECISIONS.md`
- `SHIP.md`
- `CONTEXT.md`
- `STAKEHOLDER_ASKS.md`
- `GOTCHAS.md`

The paths passed through `--spec` and `--verify` are also explicitly excluded.

This prevents the control layer from consuming the implementation budget it is
meant to supervise.

## Review and recovery

When the gate reports an overrun, use one of three paths:

1. reduce the implementation back under the accepted budget;
2. split the work into another bounded slice;
3. explicitly review and update the spec before continuing if the larger patch is
   genuinely required.

Do not enlarge the budget after the implementation is complete merely to turn the
gate green. That destroys the value of the tripwire.

## Relationship to the scope gate

A scope budget and an implementation diff budget answer different questions.

The scope gate asks:

> Did the implementation stay inside the write boundary we froze?

The diff budget asks:

> Did this patch stay near the implementation size we expected when we accepted
> the slice?

A patch can pass scope and still exceed the diff budget. That is the useful case:
all files may be allowed, yet the task grew enough to deserve another look.

## Claim boundary

A budget `PASS` means the observable implementation diff stayed within the
declared file and added-line limits under these counting rules. It does not prove
the patch is simple, correct, maintainable, or semantically within scope.
