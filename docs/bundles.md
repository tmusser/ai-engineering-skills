# Bundles

<!-- markdownlint-disable MD013 -->

Use the smallest bundle that fits. These are copy-paste shortcuts, not a new layer
of process.

`ceremony-budget` is optional. It is a router, not a required starter artifact.
Use it when the right bundle is not obvious.

All examples below use user-level installs. For project-scoped installs, replace
`--claude-user` or `--codex-user` with the project install flags described in the
README.

## Starter

Use when you want the smallest safe path for a bounded slice.

Skip when the work is just a typo, comment, or one-line fix.

Claude Code:

```bash
./install.sh --claude-user --only mini-spec,scope-freeze,build-one,verify-contract,handoff
```

Codex:

```bash
./install.sh --codex-user --only mini-spec,scope-freeze,build-one,verify-contract,handoff
```

Skills: `mini-spec`, `scope-freeze`, `build-one`, `verify-contract`, `handoff`.

## Bugfix

Use when a bug has a clear reproduction path and you want the fix to stay small.

Skip when the issue is really a redesign or you do not yet have a reproducible
failure.

Claude Code:

```bash
./install.sh --claude-user --only diagnose-loop,bug-capture,scope-freeze,build-one,test-mini,verify-contract,handoff
```

Codex:

```bash
./install.sh --codex-user --only diagnose-loop,bug-capture,scope-freeze,build-one,test-mini,verify-contract,handoff
```

Skills: `diagnose-loop`, `bug-capture`, `scope-freeze`, `build-one`, `test-mini`,
`verify-contract`, `handoff`.

## ML/data science

Use when analysis, metrics, or model work needs explicit assumptions and checks.

Skip when the task is exploratory and does not need durable verification.

This shares the same install set as dashboard work; the difference is the acceptance
criteria and verification evidence.

Claude Code:

```bash
./install.sh --claude-user --only mini-spec,checklist-mini,thin-plan,scope-freeze,build-one,test-mini,verify-contract,ship-mini,handoff
```

Codex:

```bash
./install.sh --codex-user --only mini-spec,checklist-mini,thin-plan,scope-freeze,build-one,test-mini,verify-contract,ship-mini,handoff
```

Skills: `mini-spec`, `checklist-mini`, `thin-plan`, `scope-freeze`, `build-one`,
`test-mini`, `verify-contract`, `ship-mini`, `handoff`.

## Dashboard

Use when a dashboard needs explicit acceptance criteria and a visible verification
trail.

Skip when the update is only a text tweak or a one-file fix.

This shares the same install set as ML/data science work; the difference is the
artifact being verified.

Claude Code:

```bash
./install.sh --claude-user --only mini-spec,checklist-mini,thin-plan,scope-freeze,build-one,test-mini,verify-contract,ship-mini,handoff
```

Codex:

```bash
./install.sh --codex-user --only mini-spec,checklist-mini,thin-plan,scope-freeze,build-one,test-mini,verify-contract,ship-mini,handoff
```

Skills: `mini-spec`, `checklist-mini`, `thin-plan`, `scope-freeze`, `build-one`,
`test-mini`, `verify-contract`, `ship-mini`, `handoff`.

## Agent-worker

Use when an agent will act inside a workflow with tools, side effects, or delegated
steps.

Skip when the work is a one-off and does not need autonomy boundaries.

Before scheduling or giving write access, read
[agent-worker safety](agent-worker-safety.md).

Claude Code:

```bash
./install.sh --claude-user --only constitution-lite,grill-with-docs-lite,mini-spec,scope-freeze,build-one,test-mini,verify-contract,ship-mini,handoff
```

Codex:

```bash
./install.sh --codex-user --only constitution-lite,grill-with-docs-lite,mini-spec,scope-freeze,build-one,test-mini,verify-contract,ship-mini,handoff
```

Skills: `constitution-lite`, `grill-with-docs-lite`, `mini-spec`, `scope-freeze`,
`build-one`, `test-mini`, `verify-contract`, `ship-mini`, `handoff`.

## Full governance

Use when repeated agent work, higher risk, or longer-lived state makes every
guardrail useful.

Skip when any smaller bundle fits the task. Prefer a smaller bundle unless you
already know why you need this one.

`tool-noise-guard` is passive in this bundle. Enable it when tool traffic is verbose or
repetitive; installing it does not require a compaction step on every call.

Claude Code:

```bash
./install.sh --claude-user --only grill-with-docs-lite,constitution-lite,lean-mode,context-check,tool-noise-guard,mini-spec,checklist-mini,thin-plan,scope-freeze,analyze-mini,build-one,test-mini,diagnose-loop,bug-capture,verify-contract,ship-mini,handoff
```

Codex:

```bash
./install.sh --codex-user --only grill-with-docs-lite,constitution-lite,lean-mode,context-check,tool-noise-guard,mini-spec,checklist-mini,thin-plan,scope-freeze,analyze-mini,build-one,test-mini,diagnose-loop,bug-capture,verify-contract,ship-mini,handoff
```

Skills: `grill-with-docs-lite`, `constitution-lite`, `lean-mode`, `context-check`,
`tool-noise-guard`, `mini-spec`, `checklist-mini`, `thin-plan`, `scope-freeze`,
`analyze-mini`, `build-one`, `test-mini`, `diagnose-loop`, `bug-capture`,
`verify-contract`, `ship-mini`, `handoff`.
