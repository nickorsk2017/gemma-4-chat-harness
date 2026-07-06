# TASK — 2026-07-05-subagent-call-logging
owner: Engineer
immutable: true

## Requirements
- R1: Sub-agent outcomes are invisible in mcp logs (errors only surface paraphrased in the
  synthesized answer). call_subagent must log one structured line per call: agent, tool,
  duration, ok/error (+ error text), via the standard logging module.

## Acceptance
- A1: (stub runtime) success and failure paths each emit one log record with agent, tool,
  duration and status; file compiles.
