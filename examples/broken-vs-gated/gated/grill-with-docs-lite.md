# PRE-SPEC ASSEMBLY Example

Request intent:

- Clean up duplicate auth-state handling without changing the user-visible login or refresh contract.
- Leave dashboard usability for a separate slice.

Authority map:

- `tests/auth_refresh.py` — governs: authenticated refresh behavior — task-specific delta: none
- `src/auth/session.ts` — governs: current session-state implementation — task-specific delta: remove duplicate state handling
- `src/router.ts` — governs: post-login redirect target — task-specific delta: none

Source-backed facts:

- FACT — refresh keeps an authenticated user signed in. [`tests/auth_refresh.py::test_refresh_keeps_session`]
- FACT — two branches currently derive the same signed-in state. [`src/auth/session.ts`]
- FACT — successful login redirects to `/dashboard`. [`src/router.ts`]

Spec ingredients:

Objective candidate:

- Remove duplicate auth-state handling while preserving login, redirect, session, and refresh behavior.

Acceptance signals:

- REQUEST — duplicate login-state handling is removed.
- SOURCE — authenticated refresh still preserves the session. [`tests/auth_refresh.py::test_refresh_keeps_session`]
- SOURCE — successful login still redirects to `/dashboard`. [`src/router.ts`]

Non-goals / boundaries:

- Dashboard usability changes.
- Broader app-wide auth refactors.

Constraints / compatibility seams:

- Existing refresh and redirect behavior remain compatible.

Verification anchors:

- Existing refresh contract test.
- Existing post-login redirect test.

Primary failure mode candidate:

- Cleanup removes the duplicate branch but accidentally changes session restoration after refresh.

Invalid-if candidates:

- Any implementation requires changing the dashboard route or public login behavior.

Contradictions:

- none

Tension map:

- TENSION — cleanup simplicity ↔ refresh compatibility — evidence: `src/auth/session.ts`, `tests/auth_refresh.py` — favor cleanup: deleting both state paths risks changing restoration semantics — favor compatibility: preserving both paths defeats the cleanup — status: RESOLVED by keeping one state path and preserving the tested refresh contract

Decisions required:

- none

Assumptions carried:

- ASSUMPTION — the cleanup remains internal because the authoritative tests define unchanged external behavior.

Open unknowns:

- none

Mini-spec readiness:

READY_WITH_ASSUMPTIONS
