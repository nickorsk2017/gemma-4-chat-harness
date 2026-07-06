# TASK — 2026-07-05-subagent-args-double-wrap
owner: Engineer
immutable: true

## Requirements
- R1: Sub-agent calls fail with pydantic "Field required" at ('request','path'): the
  planner (per prompt) emits arguments already shaped {"request": {...}}, and
  subagent_client wraps them into {"request": arguments} again. Make the wrapping
  idempotent both ways: never double-wrap; unwrap if the adapter flattened the schema.

## Acceptance
- A1 (stub runtime, all 4 combos): schema-expects-request x already-wrapped -> pass-through;
  x flat -> wrap; schema-flat x wrapped -> unwrap; x flat -> pass-through.
