# Agent Worker Safety

Use `ship-mini` before an agent workflow is scheduled, delegated, or allowed to run with tools.

This is a pre-flight check, not a release process.

## When to use

Use when an agent worker can write files, send messages, trigger jobs, access data, or take side effects outside the current chat.

Use it before:

- scheduling a recurring worker
- delegating a task to another agent
- enabling write access
- turning a demo into an unattended workflow

## Default safe stance

- Read-only by default.
- Dry-run before write.
- No secrets unless explicitly needed.
- No broad data access unless scoped.
- Human approval for destructive or external side effects.
- Audit trail required for autonomous runs.

## Copy into `SHIP.md`

```markdown
## Agent worker safety

- Allowed tools:
- Forbidden tools or actions:
- Destructive operations:
- Secrets and credentials:
- PII or sensitive data access:
- Dry-run mode:
- Human approval gates:
- Audit logging:
- Rollback path:
- Owner notification:
- Stop conditions:
```

## Recovery

If any item is unclear, pause the worker, tighten scope, and run `ship-mini` again.

If the task needs broader control, pair this with `scope-freeze` and `verify-contract`.

See [ship-mini](../skills/ship-mini/SKILL.md) for the gate itself.
