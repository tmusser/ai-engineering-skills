# Unified CLI

`python scripts/aes.py` provides one thin command surface for the repository's existing deterministic tools.

It is a dispatcher, not a workflow engine. It does not infer the right route, auto-chain commands, reinterpret statuses, or replace the child tools' own help and exit-code contracts.

## Usage

```bash
python scripts/aes.py <command> [args...]
```

Available commands:

| Command | Delegates to | Purpose |
| --- | --- | --- |
| `doctor` | `scripts/workflow_doctor.py` | Inspect current workflow state and print the safest next move. |
| `scope` | `scripts/scope_gate.py` | Enforce `SCOPE.md` against the live Git diff. |
| `lineage` | `scripts/check_contract_lineage.py` | Check optional contract identity across durable workflow artifacts. |
| `drift` | `scripts/check_skill_install.py` | Check installed Claude/Codex skills against their install snapshot and this repo. |
| `verify` | `scripts/verify_gate.py` | Run the deterministic verification gate. |
| `evidence` | `scripts/render_pr_evidence.py` | Render workflow artifacts into PR-ready evidence. |
| `context` | `scripts/context_pack.py` | Generate an integrity-aware context packet. |
| `install` | `install.sh` | Install or uninstall skills through the existing wrapper. |

Arguments after the command are forwarded unchanged.

For command-specific options, use the delegated help directly through the dispatcher:

```bash
python scripts/aes.py doctor --help
python scripts/aes.py scope --help
python scripts/aes.py lineage --help
python scripts/aes.py drift --help
python scripts/aes.py verify --help
python scripts/aes.py evidence --help
python scripts/aes.py context --help
python scripts/aes.py install --help
```

## Examples

Inspect a task before continuing:

```bash
python scripts/aes.py doctor --base origin/main
```

Enforce frozen write scope:

```bash
python scripts/aes.py scope --base origin/main --strict-review
```

Check optional execution-contract lineage:

```bash
python scripts/aes.py lineage --format json
```

Check a Claude Code skill installation for drift:

```bash
python scripts/aes.py drift --target claude
```

Run deterministic verification:

```bash
python scripts/aes.py verify --base origin/main --format json
```

Render a review summary:

```bash
python scripts/aes.py evidence --base origin/main --output /tmp/PR_EVIDENCE.md
```

Generate a small context packet:

```bash
python scripts/aes.py context "fix export behavior" --budget 500
```

Install the starter workflow for Codex:

```bash
python scripts/aes.py install \
  --codex-user \
  --only mini-spec,scope-freeze,build-one,verify-contract,handoff
```

## Contract

The unified CLI intentionally has a small contract:

1. Resolve one known command.
2. Forward all remaining arguments without translation.
3. Stream the child process output directly.
4. Return the child process exit code unchanged.
5. Use the same Python interpreter for Python-backed tools.
6. Use the existing `install.sh` wrapper for install behavior rather than duplicating its target-selection logic.

The only dispatcher-owned error states are command-surface errors:

- unknown command: exit `2`
- missing target, missing `sh` for install, or process launch failure: exit `127`

## Working-directory behavior

Python-backed commands inherit the caller's working directory. This matters because `doctor`, `scope`, `lineage`, `drift`, `verify`, and `evidence` inspect either the active repository or explicitly selected install target.

The `install` command runs `install.sh` from the AI Engineering Skills repository root because the existing shell wrapper resolves its installer scripts relative to that root.

## Why no standalone `aes` executable yet?

This first CLI surface stabilizes command semantics without adding packaging or installation machinery for the CLI itself. The supported invocation is:

```bash
python scripts/aes.py ...
```

A future console entrypoint named `aes` can delegate to the same `main()` function after the interface proves stable. That packaging step should not change the command contracts above.

## Boundaries

The dispatcher does **not**:

- decide which workflow level a task needs;
- invoke several commands automatically;
- turn `REVIEW_REQUIRED` into success or failure;
- rewrite child arguments;
- merge evidence from separate tools;
- create a new workflow-state format;
- install itself on `PATH`;
- make a tool safer merely because it is invoked through `aes.py`.

The existing tools remain the sources of truth for their own semantics.
