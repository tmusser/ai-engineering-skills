---
name: lean-mode
description: Compress routine agent responses to reduce token usage while preserving commands, file paths, assumptions, risks, verification details, and next actions.
---

# Lean Mode

## Purpose

Reduce token usage without losing operational clarity.

Compress prose, not meaning.

## When to use

Use when:

- the user says "lean mode", "save tokens", "be terse", "compress", "short replies", or invokes `/lean-mode`
- the task is execution-oriented
- the user already understands the domain
- the conversation is long and token budget matters
- the agent is giving routine status, next steps, commands, or implementation guidance

Do not use when:

- the user asks for teaching or explanation
- the user asks for nuanced trade-off analysis
- ambiguity is high
- safety, security, privacy, legal, medical, or financial reasoning is needed
- the user asks for polished writing
- compression would hide uncertainty or risk

## Persistence

Once enabled, stay in lean mode for routine replies until the user says:

- "stop lean mode"
- "normal mode"
- "full reasoning"
- "explain more"

Switch temporarily to fuller prose when correctness requires nuance.

## Inputs

- User request
- Current task
- Recent context
- Commands, file paths, assumptions, risks, and verification details

## Workflow

1. Detect a lean-mode trigger or explicit request.
2. Compress routine response text.
3. Keep exact commands, file paths, assumptions, risks, verification, and next actions.
4. Switch back to fuller prose when nuance or correctness requires it.
5. Stay terse until the user exits lean mode.

## Style

- Short sentences.
- Bullets over paragraphs.
- No pleasantries.
- No motivational recap.
- No redundant caveats.
- Use arrows for cause/effect.
- Use compact labels: `Verdict`, `Do`, `Avoid`, `Command`, `Risk`, `Next`.
- Use abbreviations only when obvious: repo, config, impl, req, res, fn, env, auth, DB.
- Keep exact filenames, commands, paths, and numbers verbatim.
- Keep uncertainty explicit.

## Always preserve

Never compress away:

- assumptions
- risks
- blockers
- unresolved questions
- exact commands
- exact file paths
- validation results
- test results
- GO / NO-GO judgments
- next action
- security/privacy caveats
- model/tool limitations

## Output shape

Prefer this shape:

```text
Verdict:
...

Do:
...

Avoid:
...

Command:
...

Next:
...
```

Use only the sections that are useful. Do not force every section.

Examples

Normal

"The best next step is to run validation locally, then push the tag if the repo is clean."

Lean

"Next:

Run validation.
If clean, push tag."

Normal

"This error probably means your remote is named origin rather than upstream. You can check with git remote -v."

Lean

"Likely remote name mismatch.

Do:

git remote -v
git push origin v0.5.0"

## Outputs

- Shorter responses
- Same technical meaning
- Exact commands preserved
- Next action clear

## Stop conditions

- Response is materially shorter than normal.
- User can still act without asking for missing details.
- Assumptions, risks, commands, and verification are intact.

## Anti-patterns

- Dropping caveats that affect correctness.
- Compressing filenames or commands incorrectly.
- Removing uncertainty.
- Sounding confident when evidence is weak.
- Hiding trade-offs.
- Being terse when explanation is needed.
- Replacing verification with vague reassurance.
- Using slang that makes instructions ambiguous.
