# Worktree Agent Run

Use a git worktree when one agent task should live in its own workspace and branch
while the parent checkout stays untouched. A worktree isolates files and branch state;
it is not a security boundary.

## When to use

- You want a bounded task to stay separate from the main checkout.
- You plan to use `mini-spec`, `scope-freeze`, `build-one`, `test-mini`,
  `verify-contract`, and `handoff` for one slice.
- Another session may need to pick up the task later from a clean workspace.

## Create the worktree

Start from `origin/main` and give the branch and path task-specific names.

```bash
git fetch origin
git worktree add ../repo-task-name -b task/name origin/main
cd ../repo-task-name
```

## Suggested agent prompt

```text
Use mini-spec, scope-freeze, build-one, test-mini, verify-contract, and handoff for this task.
Stay inside this worktree and keep edits limited to the current slice.
If scope changes, stop and update the spec before continuing.
```

## Verification

Use the repo's normal proof gate inside the worktree:

```bash
python scripts/validate_repo.py
npx markdownlint-cli2 "**/*.md"
git diff --check
```

Then run the task-specific test or smoke command, record the result in `VERIFY.md`,
and leave a `HANDOFF.md` that makes the next session resumable.

## Cleanup

When the task is finished and merged or intentionally closed:

```bash
cd /path/to/parent-repo
git worktree remove ../repo-task-name
git branch -d task/name
```

Keep the branch until you are sure the work has been merged or intentionally
abandoned.

## Common traps

- Treating the worktree as a security boundary
- Forgetting that the parent checkout still exists
- Reusing a path or branch name from another worktree
- Skipping `VERIFY.md` or `HANDOFF.md`
- Letting scope drift without updating the spec first
