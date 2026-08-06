# TASK — 2026-08-06-prune-abandoned-rate-limit-task
owner: Engineer
immutable: true

## Requirements
- R1: Remove `.claude/tasks/DONE/2026-08/2026-08-05-rate-limit/` from the repo. It
  is stale abandoned-task wreckage: its STATE.yaml reads `stage: INIT,
  status: PENDING` (never reached EXECUTED) yet the directory sits in the `DONE/`
  archive, which the harness invariant states holds only closed `DONE/PASS` work.
  It was never closed via `runner.py done`, so it bypassed that gate. It is
  confirmed superseded/abandoned: `2026-08-05-rate-limit-gateway-orchestrator`
  (stage DONE, status PASS) explicitly states in its own Constraints section that
  it "Supersedes the hand-rolled token-bucket design from the earlier, abandoned
  2026-08-05-rate-limit task ... that task never reached EXECUTED and no
  rate-limit code exists in the current tree."

## Acceptance
- A1: `.claude/tasks/DONE/2026-08/2026-08-05-rate-limit/` no longer exists.
- A2: `.claude/tasks/DONE/2026-08/2026-08-05-rate-limit-gateway-orchestrator/` is
  untouched (it is the valid, completed, PASS task and the current source of
  truth for rate limiting).
- A3: No other file in the repo changes.

## Constraints
- This is a deletion-only cleanup task; no code or other artifacts change.
