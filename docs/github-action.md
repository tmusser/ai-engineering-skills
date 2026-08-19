# Reusable GitHub Action

The root `action.yml` exposes the existing AI Engineering Skills evidence stack as
a reusable composite GitHub Action.

It is intentionally a thin distribution surface. The Action delegates to
`scripts/render_github_step_summary.py`, which already composes the workflow doctor
and PR evidence renderer. It does not add a new status model, workflow artifact,
or enforcement policy.

## Quick start

The consuming workflow must check out its repository before invoking the Action.
Use full history when `base` should drive deterministic diff-aware checks.

```yaml
permissions:
  contents: read

steps:
  - name: Check out repository
    uses: actions/checkout@v4
    with:
      fetch-depth: 0

  # Run normal implementation and verification checks here.

  - name: Publish AI Engineering Skills evidence
    if: always()
    uses: tmusser/ai-engineering-skills@main
    with:
      base: ${{ github.event.pull_request.base.sha }}
```

While the Action is unreleased, `@main` is the simplest way to try it. After a
release contains `action.yml`, pin the Action to the release tag or commit policy
used by your repository.

The Action requires a runner with Bash plus Python 3 available. It uses
`GITHUB_WORKSPACE` as the repository being inspected and GitHub's
`GITHUB_STEP_SUMMARY` file as the reporting target.

## Inputs

| Input | Required | Default | Purpose |
| --- | --- | --- | --- |
| `base` | no | empty | Git base forwarded to diff-aware doctor and evidence checks. |
| `no-handoff` | no | `false` | Set to `true` to omit handoff continuation details from PR evidence. |

Example without continuation details:

```yaml
- name: Publish AI Engineering Skills evidence
  if: always()
  uses: tmusser/ai-engineering-skills@main
  with:
    base: ${{ github.event.pull_request.base.sha }}
    no-handoff: "true"
```

`no-handoff` accepts only `true` or `false`. Invalid values fail as Action
configuration errors instead of being silently interpreted.

## What the Action publishes

The Step Summary contains the same reporting surfaces as the existing script:

- workflow-doctor state and the safest next move;
- PR evidence derived from `SPEC.md`, `VERIFY.md`, and optional `HANDOFF.md`;
- deterministic diff-aware evidence when `base` is supplied;
- adapter diagnostics when child tooling cannot be launched cleanly.

The Action does not create or modify `SPEC.md`, `SCOPE.md`, `VERIFY.md`, or
`HANDOFF.md`.

## Reporting is not enforcement

The reusable Action preserves the same boundary as
`scripts/render_github_step_summary.py`: successful publication returns success
even when the underlying evidence is `FAIL` or `REVIEW_REQUIRED`.

That makes it safe to use with `if: always()` as a review surface. Repositories
that want blocking behavior should keep deterministic gates as separate workflow
steps, for example:

```yaml
- name: Enforce scope contract
  run: python scripts/scope_gate.py --base "${{ github.event.pull_request.base.sha }}" --strict-review

- name: Enforce verification contract
  run: python scripts/verify_gate.py --base "${{ github.event.pull_request.base.sha }}" --strict-review

- name: Publish AI Engineering Skills evidence
  if: always()
  uses: tmusser/ai-engineering-skills@main
  with:
    base: ${{ github.event.pull_request.base.sha }}
```

The Action does not run those gates implicitly. Publishing evidence and enforcing
a contract remain separate operations.

## Consumer repository boundary

The Action code comes from `tmusser/ai-engineering-skills`, but the repository
being inspected is the caller's `GITHUB_WORKSPACE`.

The wrapper resolves bundled AES scripts from the Action checkout and passes the
consumer workspace explicitly to the Step Summary renderer. This avoids requiring
the consumer repository to copy `scripts/render_github_step_summary.py` or its
child tools into its own tree.

The consumer still owns its workflow artifacts and checkout state. If `base` is
supplied, make sure that commit is available locally; `fetch-depth: 0` is the
straightforward pull-request setup.

## Failure behavior

The Action returns a non-zero infrastructure/configuration result when it cannot
perform the reporting operation, including:

- missing `GITHUB_WORKSPACE`;
- missing Python;
- invalid `no-handoff` input;
- missing or unsafe Step Summary target;
- failure to launch the underlying reporting tools.

Non-green workflow evidence is not itself an Action infrastructure failure.

## Raw script usage remains supported

Repositories that already vendor or otherwise have the AES scripts available can
continue calling the renderer directly:

```bash
python scripts/render_github_step_summary.py --base origin/main
```

See [GitHub Step Summary integration](github-step-summary.md) for the underlying
reporting contract and local-preview behavior.
