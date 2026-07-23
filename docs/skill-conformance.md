# Skill Conformance Profile

The repository validator checks broad structure. The skill conformance profile checks a
smaller question: do the core workflow skills still expose the contract signals that
other agents, wrappers, and reviewers depend on?

## What it checks

`conformance/skill-contracts.json` contains a versioned set of required signals for the
core durable route:

- `ceremony-budget`
- `mini-spec`
- `scope-freeze`
- `verify-contract`
- `handoff`

Run the checker with:

```bash
python scripts/check_skill_conformance.py
```

The command exits zero only when every profiled skill contains its required signals and
none of its forbidden signals.

## Why this is separate from repository validation

Repository validation answers structural questions such as:

- Does every required skill exist?
- Does each skill have frontmatter and standard headings?
- Are required templates and scripts present?

Conformance answers behavioral-contract questions such as:

- Does scope control still name allowed writes and review triggers?
- Does verification still distinguish `PASS`, `FAIL`, and `REVIEW_REQUIRED`?
- Does handoff still require a resume packet and exactly one next task?
- Does ceremony routing still avoid creating a budget artifact by default?

A skill can be structurally valid while silently losing one of those guarantees.

## Claim boundary

Passing this profile does not prove that an agent follows the skill, completes tasks
correctly, or outperforms another workflow.

It proves only that the repository's published skill text retains a small set of
portable contract signals. `agent-workflow-bench` remains the place to study workflow
behavior, artifacts, verification discipline, and fresh-session resumability.

## Profile design

The first profile deliberately uses exact text signals rather than a larger parser.
That keeps the gate:

- standard-library only
- easy to audit
- portable across CI environments
- explicit about which wording is part of the contract

Add a signal only when another skill, wrapper, test, or documented workflow genuinely
depends on it. Do not turn every sentence into a compatibility promise.

## Updating the profile

When intentionally changing a required signal:

1. update the skill and profile in the same pull request
2. explain why the contract changed
3. preserve or replace the underlying guarantee
4. run repository validation and the conformance checker
5. treat accidental signal removal as a failing change

Profile versions should change only when the profile schema or interpretation changes,
not for every added signal.
