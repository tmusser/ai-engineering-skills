# Agent Worker Safety

<!-- markdownlint-disable MD013 -->

Use `ship-mini` when an agent worker is about to cross a material activation boundary.
This is an operational pre-flight check, not a second verification or release-management
framework.

This doc does not make autonomous agents safe by itself. It gives you a compact way
to make permissions, side effects, evidence, rollback, and stop conditions explicit
before the risky activation happens.

## When to use

Use this when activating an agent worker that can materially:

- write production or shared state
- send messages or publish outputs
- trigger jobs or external actions
- access secrets, credentials, PII, or sensitive data
- call tools with meaningful side effects
- run on a schedule or without interactive supervision
- perform destructive or difficult-to-reverse actions

Skip `ship-mini` for one-off interactive work that remains local, reviewable, and easy to
reverse, even when an agent or tool is involved. Delegation or tool use alone is not enough;
the activation boundary is what matters.

## Default safe stance

Start here unless you have a clear reason to loosen the boundary:

- read-only by default
- dry-run before write
- no secrets unless explicitly needed
- no broad data access unless scoped
- human approval for destructive or external side effects
- audit trail required for autonomous runs with material side effects
- explicit owner notification when an unattended run succeeds, fails, or stops early
- clear rollback or disable path before material writes are allowed

## Use with ship-mini

First establish implementation correctness with `verify-contract`. Do not replay those tests
inside `ship-mini` unless the activation environment or inputs invalidate the prior evidence.

When material activation risk is present, run `ship-mini` before enabling that risk and answer
the operational questions in `SHIP.md`.

The review should cover:

- activation surface
- allowed tools / actions
- forbidden tools / actions
- target environment or shared state
- destructive operations
- secrets and credentials
- PII or sensitive data access
- dry-run or staged activation
- human approval gates
- audit logging
- rollback or disable path
- owner notification
- stop conditions

Keep the answers short. The goal is to make the activation boundary inspectable, not to
create a large release process.

## Copy into SHIP.md

```markdown
## Agent-worker activation check

- Verification reference:
- Activation surface:
- Environment / shared state:
- Autonomy level:
- Allowed tools / actions:
- Forbidden tools / actions:
- Destructive operations possible? yes/no
- Secrets or credentials needed? yes/no
- PII or sensitive data access? yes/no
- Data scope:
- Dry-run / staged activation:
- Human approval required before write/external side effect? yes/no
- Audit log location:
- Rollback / disable path:
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
- unsupervised shared-state writes
- hidden credentials
- repeated scheduled runs without alerting
- external side effects without rollback

## Related docs

- [Limitations](../LIMITATIONS.md)
- [Bundles](bundles.md)
- [`ship-mini`](../skills/ship-mini/SKILL.md)
- [`verify-contract`](../skills/verify-contract/SKILL.md)
