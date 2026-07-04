# TASK — example-task
owner: Engineer
immutable: true

## Requirements
- R1: Add rate limiting to POST /api/login (5 attempts / 15 min / IP).
- R2: Return HTTP 429 with `Retry-After` header when exceeded.
- R3: Counter must be shared across app instances.

## Acceptance
- A1: 6th attempt within window -> 429.
- A2: Counter resets after window.
- A3: Existing login success path unchanged.

## Constraints
- No new datastore; reuse existing Redis.
- No breaking API changes.
