# GitHub Step Summary integration

`render_github_step_summary.py` publishes the current workflow state and PR evidence
into GitHub Actions' built-in Step Summary surface.

The adapter is reporting-only. It does not post PR comments, request write
permissions, install hooks, change workflow artifacts, or convert a
`REVIEW_REQUIRED` result into `PASS`.

For repositories that do not vendor the AES scripts, the root reusable Action now
wraps this same reporting path:

```yaml
- name: Publish AI Engineering Skills evidence
  if: always()
  uses: tmusser/ai-engineering-skills@main
  with:
    base: ${{ github.event.pull_request.base.sha }}
```

See [Reusable GitHub Action](github-action.md) for the consumer-facing contract,
inputs, checkout requirements, and failure behavior. The raw script integration
below remains supported.

## What it combines

The summary contains:

- `scripts/workflow_doctor.py` output, including repository/artifact state and the
  safest next move;
- `scripts/render_pr_evidence.py` Markdown, including recorded verification,
  deterministic verify-gate state, diff guards, remaining risk, and fresh handoff
  continuation when available.

Both child tools still own their existing semantics. The adapter only publishes
what they report.

## GitHub Actions usage

Run the summary step after the checks that produce or verify `SPEC.md`, `SCOPE.md`,
`VERIFY.md`, and optional `HANDOFF.md`.

For a pull-request workflow:

```yaml
permissions:
  contents: read

steps:
  - name: Check out repository
    uses: actions/checkout@v4
    with:
      fetch-depth: 0

  # Run normal implementation and verification steps here.

  - name: Publish workflow evidence summary
    if: always()
    run: >-
      python scripts/render_github_step_summary.py
      --base "${{ github.event.pull_request.base.sha }}"
```

`fetch-depth: 0` makes the PR base commit available to the deterministic diff
checks. `if: always()` lets the reporting step run even when an earlier check
failed, so the Actions page can still show the available evidence.

GitHub supplies `GITHUB_STEP_SUMMARY` automatically. The adapter appends rather
than overwrites, so it can coexist with other job-summary content. The summary
target must remain outside the repository checkout so publishing evidence cannot
dirty live workflow state or stale a previously fresh handoff.

## Reporting is not enforcement

The adapter returns `0` after it successfully publishes a summary even when the
workflow doctor or evidence renderer reports `FAIL` or `REVIEW_REQUIRED`.

That is intentional. Summary rendering should not become a second, implicit gate.
Run the existing deterministic gates separately when CI should block, for example:

```yaml
- name: Enforce scope contract
  run: python scripts/scope_gate.py --base "${{ github.event.pull_request.base.sha }}" --strict-review

- name: Enforce verification contract
  run: python scripts/verify_gate.py --base "${{ github.event.pull_request.base.sha }}" --strict-review

- name: Publish workflow evidence summary
  if: always()
  run: python scripts/render_github_step_summary.py --base "${{ github.event.pull_request.base.sha }}"
```

This keeps the ownership boundary explicit:

- gates decide whether CI blocks;
- the Step Summary makes current evidence visible;
- no bot comment or PR mutation is required.

## Missing or incomplete artifacts

Missing artifacts remain visible as incomplete or review-required evidence. The
adapter does not synthesize a green result.

This means the same reporting step can remain in a workflow across light and heavy
routes. A small task without durable artifacts will produce an honest incomplete
summary rather than silently manufacturing proof.

## Handoff behavior

By default the workflow doctor still inspects `HANDOFF.md`, and the PR evidence
renderer includes it only when present and fresh enough to trust.

Use `--no-handoff` when the published PR summary should omit continuation details:

```bash
python scripts/render_github_step_summary.py --base origin/main --no-handoff
```

The doctor still diagnoses live workflow state; `--no-handoff` only omits
continuation content from the PR evidence section.

## Local preview

Outside GitHub Actions, supply an explicit summary file outside the repository:

```bash
python scripts/render_github_step_summary.py \
  --base origin/main \
  --summary /tmp/aes-step-summary.md
```

The adapter appends Markdown to that file using the same rendering path used in
Actions. In-repository targets are rejected to keep reporting from modifying the
state it just inspected.

## Exit behavior

- `0`: the summary was published, regardless of the underlying workflow status;
- `2`: the summary target was unavailable, unsafe, could not be written, or a
  child tool could not be launched.

Underlying workflow statuses remain visible in the summary and should be enforced
through their existing commands rather than through this reporting adapter.
