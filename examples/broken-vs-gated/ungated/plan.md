# Ungated Plan

Request:

> Clean up the auth flow and make the dashboard easier to use.

## Plan

1. Inspect auth middleware and login-state handling.
2. Simplify login redirect flow.
3. Review dashboard screens and adjust layout to feel easier to use.
4. Remove dead utility code uncovered during the change.
5. Update tests after implementation.
6. Run the full test suite and fix whatever breaks.

## Problem

This looks reasonable, but it bundles multiple tasks and leaves the actual success condition vague.
