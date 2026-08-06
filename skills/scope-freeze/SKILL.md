---
name: scope-freeze
description: Explicitly limit blast radius before any implementation or file changes.
---

# Scope Freeze

## Purpose

Prevent uncontrolled changes by defining a narrow, enforceable boundary. This freezes **write scope**, not discovery.

## When to use

Immediately before editing files or running state-changing commands.

## Inputs

- SPEC.md / PLAN.md / TODO.md
- Selected task
- Current repo state
- Git base used to judge the implementation diff

## Workflow

1. Name the exact task.
2. List **allowed** files/folders as exact paths, directory prefixes, or globs.
3. List **read-only** files/folders.
4. List **forbidden** paths and operations.
5. Set max files changed and rename/deletion rules when helpful.
6. List allowed commands.
7. List compatibility seams and test-integrity triggers before editing.
8. Define clear stop condition.
9. Note that reads/searches are allowed unless explicitly forbidden.
10. Persist the canonical block as `SCOPE.md` before the first implementation write when the route invokes `scope-freeze` and `scripts/scope_gate.py` is available.
11. After the implementation diff is complete, run:

    ```bash
    python scripts/scope_gate.py --base <frozen-base>
    ```

12. Treat scope-gate `FAIL` as a hard stop: revert the violating write or renegotiate scope before continuing. Treat `REVIEW_REQUIRED` as unresolved review, not implicit permission.

Do not widen `SCOPE.md` after an out-of-scope change merely to make the gate pass. A legitimate scope expansion must be surfaced and agreed before the newly allowed write.

## Outputs

**Canonical output block:**

```text
SCOPE FREEZE
Task: ...
Allowed writes: ...
Read-only: ...
Forbidden: ...

Compatibility seams to preserve:
- Public imports / APIs: ...
- CLI behavior: ...
- Output schema: ...
- Fixture/data meaning: ...
- Existing tests that must remain meaningful: ...

Test integrity:
- Existing tests may be added to: yes/no
- Existing tests may be changed only if: ...

Review required if:
- tests changed
- dependencies changed
- protected paths touched
- compatibility seams changed

Max files changed: ...
Renames allowed: yes/no
Deletions allowed: yes/no

Allowed commands: ...
Stop when: ...
Invalid if: ...
```

Use path/glob entries for the machine-enforceable portions of `Allowed writes`, `Read-only`, and `Forbidden`. Non-path forbidden operations remain part of the human contract but cannot be proven by a file-diff gate.

See [Deterministic Scope Gate](../../docs/scope-gate.md) for status semantics and supported review triggers.

## Success looks like

- The canonical block above exists before implementation writes.
- The final live diff receives scope-gate `PASS`, or an explicit human resolves every `REVIEW_REQUIRED` trigger.
- No violating write is justified retroactively by silently widening the scope artifact.

## Stop conditions

- Scope is narrow enough for safe implementation.
- Task requires changes outside boundary → pause and renegotiate before the write.
- Scope gate returns `FAIL` → stop, revert, or renegotiate.
- Scope gate returns `REVIEW_REQUIRED` → obtain the named review before claiming completion.

## Anti-patterns

- Roaming the entire repo for a small fix.
- Expanding scope because "nearby code looked easy."
- Running write commands before boundary is agreed.
- Editing `SCOPE.md` after a violation to manufacture compliance.
- Treating an allowed path as proof that all behavior inside it is authorized.
- Forbidding necessary discovery reads.
