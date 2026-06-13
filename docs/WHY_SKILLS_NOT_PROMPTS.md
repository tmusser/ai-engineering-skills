# Why Skills, Not Prompts

A prompt asks for behavior once.
A skill makes behavior repeatable across sessions.
Templates preserve state.
Verification artifacts make claims auditable.

That difference matters when you are working with coding agents. A one-off prompt can be useful for a single reply, but it does not give the next session a stable operating shape. A reusable skill does.

In this repo, a skill is a small, named procedure with a clear trigger, a short workflow, and a known stop point. It is meant to be invoked again later with the same expectations. That is why the repo keeps skills, templates, and verification artifacts separate:

- Skills describe the repeatable behavior.
- Templates hold the durable state a session needs to resume.
- Verification artifacts record what was checked and what passed.

This keeps the workflow usable after the chat scrolls away. It also makes the process easier to audit, because the evidence lives in files instead of memory.

## What a prompt can do

A prompt can get an agent started quickly. It can shape tone, suggest a checklist, or ask for a specific output. That is helpful, but it is also fragile.

A prompt depends on the current conversation. Once the session changes, the prompt may no longer be visible, remembered, or followed the same way. It can be hard to tell whether the agent actually did the thing or just sounded confident.

## What a skill can do

A skill gives the same behavior a stable home.

It tells the agent when to use the procedure, what inputs it needs, how to work, what to output, and when to stop. Because the skill is stored as a file, it can be reused across sessions and projects. It can also be paired with templates and verification notes so the next session does not need to reconstruct the whole situation from chat.

## Failure modes this catches

- Scope creep
- Fake verification
- Unrelated file edits
- Lost handoff context
- Debugging without reproduction

These are not rare edge cases. They are the usual ways agent work goes off track when the workflow is only a prompt. A reusable skill, plus state and verification files, gives you a better chance of noticing the drift early.

## The practical rule

Use prompts for one-off direction.
Use skills when you want the behavior to be repeatable.
Use templates when the next session needs durable context.
Use verification when the work should be auditable.

That is the basic design of this repo.
