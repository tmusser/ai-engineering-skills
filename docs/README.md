# Documentation

[Back to the project](../README.md)

Start with the [quickstart](../README.md#try-it-in-60-seconds), then open the
guide that matches your task. Installing a skill makes it available; it does not
make it a required workflow stage.

## Install and choose a route

| Need | Guide |
| ---- | ----- |
| Install, update, or remove skills | [Claude Code](claude-code-installation.md) · [Codex CLI](codex-installation.md) |
| Choose a copy-paste install set | [Bundles](bundles.md) |
| Decide how much process a task needs | [Ceremony budget](ceremony-budget.md) |
| Find a skill by purpose | [Skill map](skill-map.md) |
| Follow a workflow for a concrete task | [Recipes](recipes.md) |

## Inspect and verify work

| Need | Guide |
| ---- | ----- |
| Find deterministic tool commands | [Unified CLI](unified-cli.md) |
| Inspect current workflow state | [Workflow doctor](workflow-doctor.md) |
| Check a specification or frozen write scope | [Spec gate](spec-gate.md) · [Scope gate](scope-gate.md) |
| Check artifact identity or installed-skill drift | [Contract lineage](contract-lineage.md) · [Install drift](skill-install-drift.md) |
| Prepare evidence for review | [PR evidence summary](pr-evidence-summary.md) |
| Publish existing evidence in CI | [GitHub Action](github-action.md) · [Step Summary](github-step-summary.md) |

## Keep context and autonomy bounded

| Need | Guide |
| ---- | ----- |
| Load only the relevant workflow guidance | [Context isolation](context-isolation.md) · [Route steering](context-route-steering.md) |
| Build a context packet | [Context hydration](context-hydration.md) |
| Decide what should survive a session | [Persistence horizons](context-persistence-horizons.md) |
| Recover from repeated loops | [Loop governance](loop-governance.md) |
| Run an isolated worktree task | [Worktree agent run](worktree-agent-run.md) |
| Bound a scheduled or delegated worker | [Agent-worker safety](agent-worker-safety.md) |

## Examples and evidence

* [Small dashboard](../examples/small-dashboard-poc.md),
  [ML model](../examples/ml-model-poc.md), and
  [agent worker](../examples/agent-worker-poc.md): concrete workflow artifacts.
* [Runnable examples](../examples/): inspect the scenario folders, or run
  `python scripts/run_runnable_examples.py` from the repository root.
* [Benchmark findings](benchmark-findings.md): what the pilot evidence supports.
* [Context-to-action case study](case-study-context-to-action-skills.md): applied
  workflow experience.
* [Limitations](../LIMITATIONS.md): where skills and evidence can still fail.

For changes to this repository, see [Contributing](../CONTRIBUTING.md).
For version history, see the [changelog](../CHANGELOG.md) and
[release notes](releases/README.md).
