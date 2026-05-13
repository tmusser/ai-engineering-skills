# AI Engineering Skills

A compact workflow for shipping small AI-assisted software projects with bounded scope, durable context, reproducible verification, and fast handoff.

## What this repo is

This repo is a small skill system for solo AI engineers, data scientists, and technical builders using coding agents to ship focused tools, ML workflows, agent workflows, dashboards, notebooks, and automation projects.

It helps an agent move from unclear request to usable result without losing the thread. The system favors semantic clarity before implementation, mini-specs, vertical slices, one-task implementation loops, blast-radius control, deterministic verification, bug diagnosis, and context compression.

## What this repo is not

This is not a generic prompt collection. It is not a heavyweight product process, a replacement for engineering judgment, or a framework for managing large teams. It is meant for small projects where fast progress still needs evidence, limits, and handoff notes.

## Quickstart

In a target project, install these as repo-scoped Codex skills:

```bash
mkdir -p .agents/skills docs/ai-workflow
cp -R /path/to/ai-engineering-skills/skills/* .agents/skills/
cp -R /path/to/ai-engineering-skills/templates/* docs/ai-workflow/
```

Then ask Codex:

```text
Use $grill-with-docs-lite, then $mini-spec and $thin-plan for this project. Stop before implementation.
```

Use `docs/ai-workflow/` for durable project state, or copy the templates to the project root if that is easier for the repo.

## Core workflow

Use the full path when a project may change behavior, data, user decisions, or scheduled work:

1. `grill-with-docs-lite`
2. `mini-spec`
3. `thin-plan`
4. `scope-freeze`
5. `build-one`
6. `test-mini`
7. `verify-contract`
8. `ship-mini` if user-facing, scheduled, autonomous, or decision-impacting
9. `handoff`

Emergency/debug workflow:

1. `diagnose-loop`
2. `bug-capture`
3. `verify-contract`
4. `handoff`

Prefer one working vertical slice over a broad partial system. Stop after one task. Prove the behavior. Record the command output.

## Skill routing table

| Need | Skill |
| --- | --- |
| Clarify vague goals, terms, assumptions, or non-goals | `grill-with-docs-lite` |
| Turn a clarified request into a small durable spec | `mini-spec` |
| Break work into 3-7 observable slices | `thin-plan` |
| Limit files, commands, and blast radius before coding | `scope-freeze` |
| Implement exactly one planned slice | `build-one` |
| Add focused tests, fixtures, smoke checks, or demos | `test-mini` |
| Debug a failure without random edits | `diagnose-loop` |
| Preserve discovered bug details | `bug-capture` |
| Record proof that work passed | `verify-contract` |
| Decide GO / NO-GO for use | `ship-mini` |
| Compress context for the next session | `handoff` |

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

ML workflow POC:

1. Define the split, target, feature schema, baseline, and metric.
2. Build one reproducible training/evaluation slice.
3. Verify metric calculation against a fixture.
4. Record model artifact/version and data freshness.
5. Use `ship-mini` before scheduling or using outputs for decisions.

## Recommended daily loop

Start by reading `CONTEXT.md`, `SPEC.md`, `PLAN.md`, `TODO.md`, and `HANDOFF.md` if they exist. Pick one task. Freeze the scope. Build the smallest useful change. Run the relevant checks. Update `VERIFY.md`, then update `HANDOFF.md` before ending the session.

## Full ceremony vs mini ceremony

Use full ceremony when work is user-facing, scheduled, autonomous, decision-impacting, data-sensitive, or hard to inspect manually.

Use mini ceremony for small local helpers, one-off analysis, isolated refactors, or throwaway experiments. Even then, keep a short spec, one vertical task, and a verification note.

## How to install/use with coding agents

For Codex repo-scoped usage, copy each skill directory into `.agents/skills/` in the target project. Start new projects by copying the templates from `templates/` into `docs/ai-workflow/` or the project root. Ask the agent to run the relevant skill by name and to update the matching durable artifact.

For this repository, future agents should read `AGENTS.md` before editing.

## License and acknowledgments

This repository is MIT licensed. See `LICENSE`.

This project is independently written and acknowledges inspiration from Addy Osmani's `agent-skills` and Matt Pocock's `skills`. See `ACKNOWLEDGMENTS.md`.
