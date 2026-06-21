# Agent Worker Safety

<!-- markdownlint-disable MD013 -->

Use `ship-mini` before an agent workflow is scheduled, delegated, or allowed to run
with tools. This is a pre-flight check, not a release-management framework.

This doc does not make autonomous agents safe by itself. It gives you a compact way
to make permissions, side effects, evidence, rollback, and stop conditions explicit
before the workflow runs.

## When to use

Use this when an agent worker can:

- write files
- send messages
- trigger jobs
- access data
- call external tools
- modify shared state
- run on a schedule
- take side effects outside the current chat

Skip this doc for one-off interactive edits that are read-only, local, and easy to
review manually.

## Default safe stance

Start here unless you have a clear reason to loosen the boundary:

- read-only by default
- dry-run before write
- no secrets unless explicitly needed
- no broad data access unless scoped
- human approval for destructive or external side effects
- audit trail required for autonomous runs
- explicit owner notification when a run succeeds, fails, or stops early
- clear rollback path before writes are allowed

## Use with ship-mini

Before scheduling, delegating, or enabling tool access, run `ship-mini` and answer the
agent-worker safety questions in `SHIP.md`.

The review should cover:

- allowed tools
- forbidden tools or actions
- destructive operations
- secrets and credentials
- PII or sensitive data access
- dry-run mode
- human approval gates
- audit logging
- rollback path
- owner notification
- stop conditions

Keep the answers short. The goal is to make the boundary inspectable, not to create a
large release process.

## Copy into SHIP.md

```markdown
## Agent-worker safety check

- Autonomy level:
- Allowed tools:
- Forbidden tools/actions:
- Destructive operations possible? yes/no
- Secrets or credentials needed? yes/no
- PII or sensitive data access? yes/no
- Data scope:
- Dry-run command or fixture:
- Human approval required before write/external side effect? yes/no
- Audit log location:
- Rollback path:
- Owner to notify:
- Stop conditions:
- GO / NO-GO:
```

## Practical examples

Safer:

- read from one labeled queue
- dry-run proposed changes into a file
- require human approval before writing back
- log every action and skipped action
- stop after one failed assumption

Riskier:

- broad inbox, repo, or database access
- unsupervised writes
- hidden credentials
- repeated scheduled runs without alerting
- external side effects without rollback

## Related docs

- [Limitations](../LIMITATIONS.md)
- [Bundles](bundles.md)
- [`ship-mini`](../skills/ship-mini/SKILL.md)
- [`verify-contract`](../skills/verify-contract/SKILL.md)
