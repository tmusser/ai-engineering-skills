# Specification Gate

`scripts/spec_gate.py` checks whether `SPEC.md` is concrete enough to serve as an auditable execution contract.

The gate validates **auditability**, not product truth. It can establish that a specification contains inspectable boundaries and evidence targets; it cannot prove that the user chose the right requirements.

## Why this exists

Downstream scope and verification checks are only as meaningful as the specification they are checked against. A file named `SPEC.md` is not automatically a usable contract.

The gate answers one narrow question:

> Is this specification concrete enough that a reviewer can later determine whether implementation stayed inside it and satisfied it?

## Usage

```bash
python scripts/spec_gate.py
python scripts/spec_gate.py --format json
python scripts/spec_gate.py --strict-review
python scripts/aes.py spec --strict-review
```

Use `--root` when local authoritative references should be resolved against a repository other than the current working directory. Use `--spec` to select a non-default spec path.

## Required audit floor

A usable spec must contain concrete content for:

- objective;
- acceptance criteria;
- non-goals;
- spec ceiling;
- primary failure mode;
- verification demo;
- invalid-if constraints.

Acceptance criteria should be expressed as list items so individual requirements can be reviewed and proved independently.

The checker inspects only fields that make the active contract auditable. It does not globally reject every `_TBD_` token because optional identity, loop, compatibility, or command sections may legitimately be unused.

## Authoritative references

Authoritative references remain optional. When none apply, omit the section or state that there are none.

When references are declared in the standard table, the gate checks that:

- the reference is not still the template placeholder;
- governed behavior is identified;
- the task-specific delta is resolved;
- exact local file references exist relative to `--root`.

URLs, symbols that cannot be resolved safely, and non-file artifacts are not fetched or semantically validated. The gate does not pretend that a reachable reference is necessarily the correct authority.

## Status semantics

### `PASS`

The deterministic audit floor is present and no unresolved review signal was detected.

### `FAIL`

The spec is objectively unusable as an audit contract. Examples include:

- missing `SPEC.md`;
- a missing required section;
- `_TBD_` in a required audit field;
- no primary failure mode;
- no verification demo;
- a declared exact local authoritative reference that does not exist.

### `REVIEW_REQUIRED`

The checker found something suspicious that requires judgment rather than deterministic rejection. Examples include:

- acceptance criteria written only as prose rather than auditable items;
- a criterion such as `Works correctly`;
- a placeholder or unresolved authoritative-reference row;
- unresolved open questions.

Review does not mean the specification is wrong. It means the gate cannot establish a clean audit boundary without a human decision.

## Exit codes

By default:

- `PASS` -> `0`
- `FAIL` -> `1`
- `REVIEW_REQUIRED` -> `0`

Use `--strict-review` to make `REVIEW_REQUIRED` exit `2`, matching the repository's human-review-friendly gate pattern.

## Boundaries

The specification gate does **not**:

- decide whether the requested product behavior is correct;
- invent missing requirements;
- compare implementation against the spec;
- enforce file-write scope;
- replace `scope_gate.py`, `verify_gate.py`, or contract lineage;
- fetch external references;
- require optional contract IDs;
- require unused template sections;
- add hooks, runtime interception, background checks, or automatic mutations.

A later integration can make successful downstream verification conditional on a green specification gate. That composition is intentionally outside this first PR so the checker can establish its own contract independently.
