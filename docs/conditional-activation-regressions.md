# Conditional Activation Regressions

Conditional skills should activate because a real task risk exists, not because a nearby signal merely resembles one.

This adversarial suite protects that boundary with six false-signal cases and positive controls drawn from the main workflow route fixtures.

## Protected non-triggers

| False signal | Must not activate | Actual trigger |
| --- | --- | --- |
| No prior analysis exists | `analyze-mini` | stale task-defining inputs or another implementation-shaping analysis trigger |
| The conversation is long | `workspace-checkpoint` | a specific consequential next action with competing governing constraints |
| Verified work will be released normally | `ship-mini` | material activation risk such as shared-state writes, autonomy, permissions, or irreversible effects |
| The task completed successfully | `handoff` | another session or agent must continue, or unresolved work needs durable resume state |
| Optional skills are installed | any conditional skill | the skill's own named risk or ownership trigger |
| Verification passed | `teach-back` | the human wants or needs ownership transfer from the verified implementation |

The installed-skill case covers every conditional skill currently registered by `scripts/check_route_contracts.py`: `analyze-mini`, `constitution-lite`, `handoff`, `ship-mini`, `teach-back`, `test-mini`, `thin-plan`, and `workspace-checkpoint`.

## How the suite works

Each case in `tests/fixtures/conditional_activation_regressions.json` records:

- a false signal;
- the conditional skill or skills that must remain off;
- the source-backed contract language defining that boundary;
- a valid light route that explicitly skips the skill;
- an existing positive-control scenario where the skill is correctly selected because its real trigger exists.

The tests then perform two checks:

1. The false-signal route passes the existing workflow route checker with the conditional skill absent.
2. Mutating that route to invoke the skill without adding its real trigger is rejected.

Positive controls prevent the suite from becoming a blanket ban. The same skills must remain valid when their declared trigger is present.

## Run it

```bash
python -m unittest discover tests -p 'test_conditional_activation_regressions.py' -v
```

The full repository test discovery also includes the suite:

```bash
python -m unittest discover tests
```

## Adding a regression

Add a case only when all of these are true:

- the false signal is plausible enough to cause recurring over-ceremony;
- a repository skill or routing document explicitly says the signal is insufficient;
- the guarded skill has an existing positive-control route with a real trigger;
- selecting the skill without that trigger is rejected by the route checker.

Do not add cosmetic task variants or use the fixture as a general ontology of user intent.

## Claim boundary

Passing this suite shows that the repository's declared conditional-routing rules distinguish these known false signals from their real triggers. It does not prove that an agent will classify arbitrary natural-language tasks correctly or resist every possible form of ritual process.
