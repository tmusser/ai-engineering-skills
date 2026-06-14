# Request

> Clean up the auth flow and make the dashboard easier to use.

## Why this is risky

This sounds like one task, but it likely contains at least two:

1. auth cleanup
2. dashboard usability

Without a gate, the agent may produce a reasonable-looking plan that mixes backend/auth behavior, UI layout changes, test updates, and opportunistic cleanup into one broad patch.
