<!-- Temporary PR-scoped note; fold into CHANGELOG.md before merge if desired. -->

## Workspace checkpoint

- Adds optional `workspace-checkpoint` for last-mile reactivation of source-backed constraints before consequential actions.
- Keeps the checkpoint ephemeral: no `WORKSPACE.md`, no checkpoint ledger, no introspection or hidden-reasoning claims.
- Documents the feature as an engineering hypothesis inspired by the July 2026 Transformer Circuits global-workspace paper, not an implementation of the paper's interpretability or training methods.
- Adds conformance and pytest coverage plus routing and full-governance bundle integration.
