# Case Study: Building `context-to-action-skills`

## Goal

Create a companion repo for business users who need to turn messy context into clear facts, asks, decisions, owners, risks, updates, and safe replies.

## Why this matters

`ai-engineering-skills` is designed to reduce coding-agent chaos through scoped work, durable context, verification, and handoff.

`context-to-action-skills` applies the same operating loop to a broader audience: business users working across meetings, Slack, Gmail, Calendar, Atlassian, transcripts, and data outputs.
Its root skill, `/reduce-to-facts`, turns dense source material into a source-grounded fact ledger before any action is taken.

## Workflow used

The companion repo was built using the core `ai-engineering-skills` loop:

1. `mini-spec` — define audience, scope, constraints, and acceptance criteria
2. `thin-plan` — break the repo into small vertical slices
3. `scope-freeze` — limit each implementation slice
4. `build-one` — create one slice at a time
5. `test-mini` — validate structure and prompt quality
6. `verify-contract` — record evidence and remaining risks
7. `handoff` — preserve next-session state

## Result

The v0.1 companion repo shipped with six front-door skills:

- `brief-me`
- `clear-ask`
- `meeting-to-actions`
- `decision-brief`
- `status-update`
- `follow-up-draft`

It intentionally avoids connector-specific skill sprawl. Slack, Gmail, Calendar, Zoom transcripts, Atlassian, and Hex/data outputs are treated as context sources, not user-facing complexity.
The repo also distinguishes source-only and source-expanded modes so the user can see what is supported, what is inferred, and what still needs follow-up.

## Design lesson

The same control loop can produce different artifacts for different audiences:

- Technical users need bounded implementation, tests, verification, and handoff.
- Business users need clear facts, asks, owners, decisions, risks, updates, and follow-through.

The shared principle is durable context plus bounded action.
