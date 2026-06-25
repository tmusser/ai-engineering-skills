# AI Engineering Skills

[![CI](https://github.com/tmusser/ai-engineering-skills/actions/workflows/ci.yml/badge.svg)](https://github.com/tmusser/ai-engineering-skills/actions/workflows/ci.yml)

<!-- markdownlint-disable MD013 -->

A compact workflow for shipping small AI-assisted software projects with bounded scope,
durable context, reproducible verification, and fast handoff.

Build with AI like a disciplined team of two: one human sets direction and boundaries;
one agent executes inside them.

This is not just a prompt pack. Skills make behavior repeatable across sessions,
templates preserve state, and verification records make claims auditable. See
[Why skills, not prompts](docs/WHY_SKILLS_NOT_PROMPTS.md).

## Start here

This repo helps agents stop wandering, prove what changed, and preserve handoff state.

Use it when work is too consequential for ad hoc prompting but too small for a PRD.

The smallest starter loop is:

```text
mini-spec -> scope-freeze -> build-one -> verify-contract -> handoff
```

Recommended starter set:

- `mini-spec`
- `scope-freeze`
- `build-one`
- `verify-contract`
- `handoff`

`thin-plan` is recommended when a slice needs more shape, but it is intentionally not
part of the absolute starter path.

## Try the starter install

Clone the repo:

```bash
git clone https://github.com/tmusser/ai-engineering-skills.git
cd ai-engineering-skills
```

Install only the starter set for Claude Code:

```bash
./install.sh --claude-user --only mini-spec,scope-freeze,build-one,verify-contract,handoff
```

Then open Claude Code in a project and run:

```text
/mini-spec
/scope-freeze
/build-one
/verify-contract
/handoff
```

Install only the starter set for Codex:

```bash
./install.sh --codex-user --only mini-spec,scope-freeze,build-one,verify-contract,handoff
```

Then open Codex in a project and run:

```text
$mini-spec
$scope-freeze
$build-one
$verify-contract
$handoff
```

For project-scoped installs, replace `--claude-user` or `--codex-user` with the
project install flags described in [Installation](#installation).

## Why this exists

AI coding agents are powerful, but sessions often fail for predictable reasons:

- vague requests become plausible but wrong plans
- scope expands quietly
- weak verification gets accepted as completion
- long contexts hide the important constraint
- handoff state disappears between sessions

`ai-engineering-skills` gives the human and agent a shared set of boundaries, checks,
and durable artifacts. It reduces risk, but it does not replace judgment.

**Better specs, not bigger specs.**

## Proof artifact: agent-workflow-bench

**Proof artifact:** this repo is evaluated by
[`agent-workflow-bench`](https://github.com/tmusser/agent-workflow-bench), a small
standalone benchmark for agent skills, verification artifacts, and fresh-session
resumability.

The benchmark does not claim that workflow skills universally beat a baseline coding
agent. It tests a narrower question:

> When an agent completes messy technical work, does it leave enough verified context
> for another fresh session to trust, audit, and continue it?

Current pilot findings:

| Task | Baseline | Skill-routed | What it shows |
|---|---|---|---|
| Task 4 — Impossible Churn Regression | Green functional fix, no workflow artifacts | Green functional fix + `BUGS.md`, `VERIFY.md`, `HANDOFF.md` | Skill-routed runs can leave durable context for audit/resume |
| Task 5 — Fake Data Campaign Lift Trust | Public pass, hidden fail | Public pass, hidden fail + clearer audit/handoff trail | Skills improved visibility, but did not automatically catch denominator/leakage traps |

The intended claim boundary is:

- The skills improve auditability, verification discipline, and resumability.
- The benchmark does not prove broad pass-rate superiority.
- The benchmark is useful precisely because it exposes where the current skills still
  need better recipes, such as the Data Trust Pass and denominator-trap workflows.

The Task 5 miss directly informed the new
[`examples/denominator-trap/`](examples/denominator-trap/) demo and the Data Trust
Pass recipe in [docs/recipes.md](docs/recipes.md).

## Evaluate before installing

This repo is new, so trust should come from inspectable artifacts rather than
popularity signals.

Start here:

- [examples/broken-vs-gated](./examples/broken-vs-gated/) — compare an ungated plan
  with the gated workflow on the same task
- [examples/tiny-bugfix](examples/tiny-bugfix/README.md) — a small vertical slice
  with the workflow artifacts
- [examples/denominator-trap](examples/denominator-trap/README.md) — a compact
  data-trust example inspired by the benchmark
- [Limitations](LIMITATIONS.md) — edge cases, escape hatches, and non-promises
- [Compatibility confidence](docs/compatibility-confidence.md) — documented install
  paths, tested status, and caveats

The goal is not to make agents slower. The goal is to make their work easier to
steer, verify, resume, and discard when the direction is wrong.

## Demo

![ai-engineering-skills terminal demo](assets/demo.gif)

This sanitized terminal demo shows a bounded cycle using fake data and simulated
agent output. It is generated from `demo/demo.tape` using VHS, so it is reproducible
and does not require private data, API keys, or a real Claude Code session.

Render it with:

```bash
scripts/render_demo.sh
```

## Optional bundles

Use the smallest bundle that fits. See [docs/bundles.md](docs/bundles.md) for
copy-paste install sets for starter, bugfix, ML/data science, dashboard,
agent-worker, and full governance workflows.

## How this is different

Raw prompting gives instructions.

Plan Mode approves a plan.

`ai-engineering-skills` creates bounded, inspectable artifacts before, during,
after, and between agent sessions.

The wedge is narrow on purpose:

- gates before and after implementation
- durable files that survive restarts
- risk-calibrated ceremony for solo bounded work
- verification records instead of vibes
- handoff state for the next session or agent

This is not generic prompting advice, not heavyweight governance, and not a promise
that an agent will follow instructions perfectly.

## Common objections

### Isn't this just better prompting?

Better prompts help, but prompts are usually trapped in the chat. These skills push
important state into persistent, versionable artifacts: specs, scope boundaries,
verification records, and handoff notes. The artifact trail is the leverage.

### Why not just use Plan Mode?

Use Plan Mode. It is useful. This repo adds an earlier question before plan approval:
"is this the right bounded work?" It also adds later checks for evidence and restart
state. The tools are complementary.

### Is this process theater?

It can be if you use too much of it. Start with the five-gate starter and skip the
workflow entirely for tiny reversible edits. The repo is designed around small gates
that catch misalignment early, not ceremony for its own sake.

### Will agents ignore the skills?

Sometimes. Skills do not guarantee obedience. They make the expected behavior
explicit, inspectable, and easier to correct when the agent drifts. See
[Limitations](LIMITATIONS.md) for the honest failure modes.

### How is this different from broader agent-skill libraries?

Broad skill libraries cover many tasks and platforms. This repo is narrower and more
opinionated: a small operating loop for solo technical builders doing bounded coding,
data, dashboard, automation, or small agent work with durable verification and handoff
artifacts.

## Skill map

```mermaid
flowchart TD
  A["Clarify<br/>grill-with-docs-lite<br/>constitution-lite"] --> B["Specify<br/>mini-spec<br/>checklist-mini"]
  B --> C["Plan<br/>thin-plan<br/>analyze-mini"]
  C --> D["Constrain<br/>scope-freeze"]
  D --> E["Build<br/>build-one"]
  E --> F["Verify<br/>test-mini<br/>verify-contract"]
  F --> G["Ship<br/>ship-mini"]
  G --> H["Handoff<br/>handoff"]
  I["Diagnose<br/>diagnose-loop<br/>bug-capture"] --> D
  I --> F
```

## Context-pressure control layer

Four skills form the backbone for resilient agent sessions:

- `scope-freeze` — limits blast radius before work
- `verify-contract` — records evidence after work
- `context-check` — detects drift during work
- `handoff` — preserves durable state between sessions

Together they support bounded execution and verifiable progress.

For scheduled or delegated tool-using runs, see
[Agent-worker safety](docs/agent-worker-safety.md) before giving a workflow write
access.

## The failure mode this avoids

```mermaid
flowchart TD
  A["Vague request"] --> B["Many edits"]
  B --> C["Weak verification"]
  C --> D["Long context"]
  D --> E["Lost saliency"]
  E --> F["Buggy / bloated output"]

  G["Clarified request"] --> H["mini-spec"]
  H --> I["One vertical slice"]
  I --> J["scope-freeze"]
  J --> K["build-one"]
  K --> L["verify-contract"]
  L --> M["handoff"]
  M --> N["fresh context"]
```

## What this repo is

This repo is a portable skill pack for solo AI engineers, data scientists, and
technical builders using coding agents to ship focused tools, ML workflows, agent
workflows, dashboards, notebooks, and automation projects.

It is designed for small projects where speed still needs evidence, limits, and
handoff notes.

It emphasizes:

- semantic clarity before implementation
- mini-specs instead of bloated specs
- vertical-slice planning
- one-task implementation loops
- blast-radius control
- deterministic verification
- bug diagnosis instead of random fixing
- handoff and context compression
- lightweight ship gates for ML, agent, and dashboard workflows

## What this repo is not

This is not a generic prompt collection.

It is not a heavyweight product process.

It is not a replacement for engineering judgment.

It is not tied to one AI coding tool.

Claude Code and Codex are peer documented targets. Manual install is always
available because skills are plain folders with `SKILL.md` files.

`grill-with-docs-lite` acknowledges Matt Pocock's `grill-with-docs`, but targets a
smaller operating point. Use the full version when a plan needs to be stress-tested
against a domain model, glossary, codebase, or ADRs. Use this lite version when a
small AI-engineering task only needs enough semantic pressure to define intent,
non-goals, boundaries, and readiness before `mini-spec`.

`lean-mode` is optional. It changes communication density, not the project workflow.
Use it when token budget matters, then switch back to full reasoning when ambiguity,
safety, or trade-offs require more explanation.

`context-check` is an optional passive guardrail. It watches for drift, compaction
pressure, and active-mode loss, then recommends the smallest corrective action.

## Companion case studies

[`context-to-action-skills`](https://github.com/tmusser/context-to-action-skills)
applies the same lightweight-skill philosophy to non-technical context work: clear
facts, asks, decisions, owners, risks, updates, and safe replies.

It is useful as a companion case study: this repo focuses on technical execution with
coding agents, while `context-to-action-skills` shows how the same operating pattern
can be adapted for business-context clarity. See
[docs/case-study-context-to-action-skills.md](docs/case-study-context-to-action-skills.md).

A second case study shows the same loop guiding a real external OSS contribution for
`tmusser/skill-codex` on the `cursor-cli-delegation` branch: [Cursor CLI delegation
case study](docs/case-studies/skill-codex-cursor-delegation/README.md).

## Installation

This repo is portable by design.

Claude Code has a documented install path for slash-style invocation such as
`/mini-spec`.

Codex has a documented install path through `.agents/skills`, explicit `$skill-name`
invocation, `/skills` discovery where available, and `AGENTS.md` project guidance.

Same workflow. Native invocation style for each tool.

Compatibility confidence and invocation notes are in
[docs/compatibility-confidence.md](docs/compatibility-confidence.md).

Hardening milestones are summarized in [CHANGELOG.md](CHANGELOG.md). Maintainer
release steps are in [docs/release-checklist.md](docs/release-checklist.md).

The installers are safety-aware: each installed skill gets an
`AI_ENGINEERING_SKILLS_VERSION.json` manifest. Managed, unmodified installs update
cleanly. Unmanaged or locally modified installs are refused by default and require
`--force`. Use `--backup` before replacing or removing existing installs. `--dry-run`
stays side-effect free, `--only` narrows the selected skills, `--uninstall` removes
selected skills, and `--include-templates` keeps support files portable.

### Claude Code install

Install for your personal Claude Code environment:

```bash
./install.sh
```

Equivalent explicit command:

```bash
./install.sh --claude-user
```

Direct Python installer:

```bash
python scripts/install_claude_code.py --target user
```

Use this when you want these skills available across all Claude Code projects.

Install into a specific project:

```bash
./install.sh --claude-project /path/to/project
```

Direct Python installer:

```bash
python scripts/install_claude_code.py --target project --project-path /path/to/project
```

Use this when you want the skills versioned with a specific repo for team or
project-scoped usage.

After installation, invoke skills with slash commands such as:

```text
/mini-spec
/thin-plan
/scope-freeze
/build-one
/test-mini
/diagnose-loop
/lean-mode
/context-check
/handoff
```

Claude Code automatic skill invocation may vary by task and environment. Explicit
slash invocation is the documented path. See `docs/claude-code-installation.md` for
details.

### Codex install

Install for your personal Codex environment:

```bash
./install.sh --codex-user
```

Direct Python installer:

```bash
python scripts/install_codex.py --target user
```

Use this when you want these skills available across Codex projects.

Install into a specific project:

```bash
./install.sh --codex-project /path/to/project
```

Direct Python installer:

```bash
python scripts/install_codex.py --target project --project-path /path/to/project
```

Use this when you want the skills versioned with a specific repo for team or
project-scoped usage.

After installation, invoke skills with `$skill-name` or select them through `/skills`
where available.

Examples:

```text
$mini-spec
$thin-plan
$scope-freeze
$build-one
$verify-contract
$lean-mode
$context-check
$handoff
```

Codex invocation and discovery may vary by client behavior. Explicit `$skill-name`
invocation is the documented path. You can also ask Codex explicitly:

```text
Use $grill-with-docs-lite, then $mini-spec and $thin-plan for this project. Stop before implementation.
```

See `docs/codex-installation.md` for details.

### Manual

Each skill is just a folder with a `SKILL.md` file. To install manually:

1. Copy the skill folders you want from `skills/`.
2. Place them in the skill directory used by your AI coding tool.
3. Copy templates from `templates/` into your project when you want durable state
   files.
4. Invoke the skill by name or reference the `SKILL.md` directly.

Manual compatibility depends on whether the receiving agent reads local skill folders
and follows similar invocation conventions.

## Slash-style usage

### Claude Code slash commands

Installed Claude Code skills are invoked directly with `/skill-name`.

Available Claude Code slash commands:

```text
/grill-with-docs-lite
/mini-spec
/thin-plan
/scope-freeze
/build-one
/test-mini
/diagnose-loop
/lean-mode
/bug-capture
/verify-contract
/ship-mini
/context-check
/handoff
```

The skill folder name becomes the slash command name.

### Codex invocation

Codex skills should be invoked with `$skill-name` or selected through `/skills` where
available.

Examples:

```text
$mini-spec
$thin-plan
$scope-freeze
```

Do not use `/skill-name` for Codex unless your Codex environment has its own command
mapping.

## Why every skill includes anti-patterns

Common agent failures are predictable:

- implementing before clarifying
- expanding scope
- touching unrelated files
- debugging without reproducing
- mistaking execution for correctness
- losing context between sessions

Each skill includes anti-patterns as explicit guardrails. The goal is not extra
ceremony. The goal is to stop known failure modes before they consume the session.

## Core workflow

Use the smallest route that fits the task.

For real repo work, a common request-to-verified-work path is:

```text
mini-spec -> thin-plan -> scope-freeze -> build-one -> test-mini -> verify-contract -> handoff
```

Use `ship-mini` before user-facing, scheduled, autonomous, decision-impacting, or
sensitive work.

Optional gates:

- use `constitution-lite` before repeated project work
- use `checklist-mini` after `mini-spec`
- use `analyze-mini` before `build-one`

The optional `constitution-lite`, `checklist-mini`, and `analyze-mini` gates are
inspired by broader spec-driven development patterns, including GitHub's Spec Kit,
but adapted for smaller AI-engineering projects.

Emergency/debug workflow:

1. `diagnose-loop`
2. `bug-capture`
3. `verify-contract`
4. `handoff`

Prefer one working vertical slice over a broad partial system. Stop after one task.
Prove the behavior. Record the command output.

## Workflow recipes

Use the smallest route that fits the task. See `docs/recipes.md` for visual workflows
covering small projects, bugfixes, ML/dashboard work, agent workers, and fresh-context
development.

## Skill routing table

| Need | Skill |
| --- | --- |
| Clarify vague goals, terms, assumptions, or non-goals | `grill-with-docs-lite` |
| Set compact project rules before repeated agent work | `constitution-lite` |
| Turn a clarified request into a small durable spec | `mini-spec` |
| Validate a mini-spec before planning | `checklist-mini` |
| Break work into 3-7 observable slices | `thin-plan` |
| Limit files, commands, and blast radius before coding | `scope-freeze` |
| Check artifact consistency before implementation | `analyze-mini` |
| Implement exactly one planned slice | `build-one` |
| Add focused tests, fixtures, smoke checks, or demos | `test-mini` |
| Debug a failure without random edits | `diagnose-loop` |
| Preserve discovered bug details | `bug-capture` |
| Record proof that work passed | `verify-contract` |
| Decide GO / NO-GO for use | `ship-mini` |
| Compress context for the next session | `handoff` |
| Reduce routine response length while preserving commands, risks, verification, and next actions | `lean-mode` |
| Detect context drift, rehydration loops, active-mode loss, hypothesis sprawl, or handoff pressure | `context-check` |

## Example workflows

Dashboard POC:

1. Define the KPI, date window, grain, and filters.
2. Write a mini-spec with a fixture dataset and expected row counts.
3. Build one chart or table slice.
4. Run a deterministic check and capture a screenshot or smoke path.
5. Use `ship-mini` before anyone relies on the dashboard.

Agent worker POC:

1. Clarify autonomy level, allowed tools, forbidden operations, and handoff behavior.
2. Freeze scope around one board, queue, or ticket type.
3. Implement one action path.
4. Verify with a dry run, fixture, or test board.
5. Use `ship-mini` to review permissions and rollback.
6. See [Agent-worker safety](docs/agent-worker-safety.md) before scheduling or giving
   write access.

ML workflow POC:

1. Define the split, target, feature schema, baseline, and metric.
2. Build one reproducible training/evaluation slice.
3. Verify metric calculation against a fixture.
4. Record model artifact/version and data freshness.
5. Use `ship-mini` before scheduling or using outputs for decisions.

Cross-functional infrastructure coordination:

1. Use `grill-with-docs-lite` to turn a meeting transcript or brain dump into a clear
   technical request.
2. Track stakeholder asks in files, keep private technical context in `.local/context/`,
   and use verification scripts for access or workflow checks.
3. Keep `CONTEXT.md`, `TODO.md`, and `HANDOFF.md` current so the next session can pick
   up cleanly.

## Recommended daily loop

Start by reading `CONTEXT.md`, `SPEC.md`, `PLAN.md`, `TODO.md`, and `HANDOFF.md` if
they exist.

Pick one task. Freeze the scope. Build the smallest useful change. Run the relevant
checks. Update `VERIFY.md`, then update `HANDOFF.md` before ending the session.

## Ceremony ladder

Use the smallest workflow that still feels safe.

### Level 0 — Patch

Use for trivial, reversible changes such as typos, comments, formatting, or a tiny
single-file edit.

Workflow:

```text
edit -> run one sanity check -> record verification in the commit message
```

No workflow artifacts required.

Commit footer example:

```text
Verify: pytest -q tests/test_parser.py
Result: PASS
```

### Level 1 — Micro

Use for small bounded behavior changes, usually 1-3 files.

Workflow:

```text
inline scope-freeze -> build-one -> verify-contract
```

Use `test-mini` if behavior changed and a fast check exists.

### Level 2 — Mini

Use for small vertical slices that benefit from explicit acceptance criteria or
non-goals.

Workflow:

```text
mini-spec -> optional thin-plan -> scope-freeze -> build-one -> test-mini -> verify-contract
```

Use `handoff` if another session will continue.

Analytical deliverables such as sizing memos or scenario tables often fit Level 2:
use spec/checklist/plan/build/test, then add heavier gates only if the artifact
becomes durable, reused, or multi-session.

### Level 3 — Full

Use when work is user-facing, scheduled, autonomous, decision-impacting,
data-sensitive, hard to inspect manually, or likely to span multiple slices.

Workflow:

```text
grill-with-docs-lite -> mini-spec -> checklist-mini -> thin-plan -> scope-freeze -> analyze-mini -> build-one -> test-mini -> verify-contract -> ship-mini -> handoff
```

### Below Level 0 — Prompt primitives

Some tasks do not need a skill, artifact, or workflow gate. For quick steering moves like “Find the lie,” “Smallest safe diff,” or “Test the tests,” use prompt primitives instead.

See [Prompt primitives](docs/recipes.md#prompt-primitives).

## Part of the suite

This repo is one piece of a small set of repos for making AI-assisted work clearer,
more bounded, and more verifiable.

| Repo | Primary job | First thing to try |
| --- | --- | --- |
| [ai-engineering-skills](https://github.com/tmusser/ai-engineering-skills) | Bounded, verifiable AI coding work | `mini-spec -> scope-freeze -> build-one -> verify-contract` |
| [context-to-action-skills](https://github.com/tmusser/context-to-action-skills) | Turn messy workplace context into facts and next actions | `reduce-to-facts`, then `clear-ask`, `decision-brief`, `status-update`, or `follow-up-draft` |
| [chart-contract](https://github.com/tmusser/chart-contract) | Auditable analytical charts | Build one chart with an explicit claim, caveat, and source trail |

The shared pattern: clarify first, bound the work, verify the result, preserve handoff
state.

See [Suite map](docs/SUITE_MAP.md).

## License and acknowledgments

This repository is MIT licensed. See `LICENSE`.

This project is independently written and acknowledges inspiration from Addy Osmani's
`agent-skills`, Matt Pocock's `skills`, and GitHub's `spec-kit`. See
`ACKNOWLEDGMENTS.md`.
