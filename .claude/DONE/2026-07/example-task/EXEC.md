# EXEC — example-task
exec_version: 1
author: Executor
plan_ref: 1

## Summary
- P1: added `middleware/rateLimit.js` — Redis INCR + EXPIRE sliding window.
- P2: wired middleware into `routes/auth.js` before login handler.
- P3: 429 + `Retry-After` from key TTL.
- P4: key `rl:login:<ip>`, window=900, max=5; Redis-down -> fail-open.

## Changed Files
- A middleware/rateLimit.js
- M routes/auth.js

## Notes
- No new deps. Login success path untouched (A3).
