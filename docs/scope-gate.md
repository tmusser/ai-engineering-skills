# Deterministic Scope Gate

`scope-freeze` defines the write boundary. `scripts/scope_gate.py` compares that
persisted boundary with the live Git diff so an agent cannot treat the scope block
as a completion-time suggestion.

## Run it

Persist the canonical scope block as `SCOPE.md`, then run:

```bash
python scripts/scope_gate.py --base origin/main
```

Machine-readable output is available for CI and composed tooling:

```bash
python scripts/scope_gate.py \
  --base origin/main \
  --format json
```

Use `--strict-review` when `REVIEW_REQUIRED` should return exit code 2.

## Status semantics

- `PASS` — every governed changed path is allowed and no declared review trigger fired.
- `FAIL` — a changed path escaped allowed writes, touched a read-only or forbidden
  path, exceeded a declared file budget, or violated a declared rename/deletion rule.
- `REVIEW_REQUIRED` — the contract or Git state could not be established, or an
  observable declared review trigger fired.

Default exit codes are 0 for `PASS`, 1 for `FAIL`, and 0 for `REVIEW_REQUIRED`.
With `--strict-review`, `REVIEW_REQUIRED` returns 2.

## Enforceable contract

The gate reads the canonical fields emitted by `scope-freeze`:

```text
SCOPE FREEZE
Task: add bounded parser behavior
Allowed writes:
- src/parser.py
- tests/test_parser.py
Read-only:
- docs/**
Forbidden:
- .env
- migrations/**

Review required if:
- tests changed
- dependencies changed
- .github/workflows/**

Max files changed: 3
Renames allowed: no
Deletions allowed: no

Stop when: parser behavior and focused tests are complete
Invalid if: any write escapes the declared paths
```

Path entries support exact paths, directory prefixes, and shell-style glob patterns.
The scope artifact itself is excluded from its own write boundary so creating or
updating `SCOPE.md` does not self-fail the gate.

Recognized review triggers include:

- `tests changed`
- `fixture/data changed`
- `fixtures changed`
- `dependencies changed`
- `workflow files changed`
- `schemas changed`
- `migrations changed`

A review-trigger entry may also be an explicit path or glob.

## Agent contract

When a route invokes `scope-freeze` and files will be modified:

1. Write `SCOPE.md` before the first implementation write.
2. Do not widen the file patterns after an out-of-scope edit merely to make the
   gate pass.
3. Run the gate before declaring the slice complete.
4. On `FAIL`, stop, revert the violating write, or renegotiate scope.
5. On `REVIEW_REQUIRED`, surface the trigger and obtain the required review before
   claiming completion.

## Claim boundary

The gate enforces observable file-scope facts. It does not prove that behavior
inside an allowed file stayed under the spec ceiling, that an architectural rule
was respected, or that a forbidden semantic operation did not occur.

Non-path forbidden operations remain visible as advisory notes. Use
`verify-contract`, tests, compatibility probes, and human review for semantic
boundaries.

The contract is also not tamper-proof against an actor authorized to rewrite
`SCOPE.md`. Its purpose is deterministic consistency and fail-closed agent
behavior, not cryptographic policy enforcement.
