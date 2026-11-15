# Failure-to-Proof Demo Spec

## Objective

Export selected orders as a CSV without changing its header contract.

## Acceptance criteria

- AC-1: Matching-region orders retain the original order_id,region CSV schema.
- AC-2: Zero matching orders still produce a header-only CSV.

## Non-goals

- Do not add new columns or introduce external dependencies.
