# PLAN — example-task
plan_version: 1
author: Planner
complexity: MEDIUM

## Strategy
- P1: Add sliding-window limiter using existing Redis client (INCR + EXPIRE). [R1,R3]
- P2: Insert limiter as middleware before login handler. [R1]
- P3: On limit exceeded, respond 429 + Retry-After = TTL. [R2]
- P4: Key = `rl:login:<ip>`, window 900s, max 5. [R1]

## Impact
- files: middleware/rateLimit, routes/auth (wire middleware)
- deps: none (reuse Redis)

## Risks
- Redis unavailability -> fail-open policy (allow) to avoid lockout. [note for Executor]

## Sequence
P1 -> P2 -> P3 -> P4
