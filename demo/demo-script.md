# Demo Script

## Scene 1: Start from a clean toy workspace

- Terminal action: Create `/tmp/ai-engineering-skills-demo` and copy the fake customer CSV.
- Expected viewer takeaway: The demo is synthetic and does not rely on private code or data.

## Scene 2: Show available Claude Code slash commands

- Terminal action: Print the installed skill commands, including `/mini-spec`, `/thin-plan`, `/scope-freeze`, `/build-one`, `/verify-contract`, and `/handoff`.
- Expected viewer takeaway: The workflow is invoked as small named skills.

## Scene 3: Run `/mini-spec`

- Terminal action: Simulate `/mini-spec` output and write `SPEC.md`.
- Expected viewer takeaway: The project idea becomes a compact, durable spec.

## Scene 4: Run `/thin-plan`

- Terminal action: Simulate `/thin-plan` output and write `PLAN.md`.
- Expected viewer takeaway: The work is broken into vertical slices that can be verified.

## Scene 5: Run `/scope-freeze`

- Terminal action: Print the allowed files, forbidden operations, and stop condition.
- Expected viewer takeaway: The agent has a bounded editing surface before implementation.

## Scene 6: Run `/build-one`

- Terminal action: Simulate creating a tiny CLI output file from the fake CSV.
- Expected viewer takeaway: One bounded change is implemented and stopped.

## Scene 7: Run `/verify-contract`

- Terminal action: Write `VERIFY.md` with command output and proof of behavior.
- Expected viewer takeaway: Running code is not enough; the behavior is recorded.

## Scene 8: Run `/handoff`

- Terminal action: Write `HANDOFF.md` and preview the next task.
- Expected viewer takeaway: The next session can continue without re-explaining context.
