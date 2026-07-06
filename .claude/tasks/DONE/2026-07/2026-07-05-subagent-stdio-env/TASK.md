# TASK — 2026-07-05-subagent-stdio-env
owner: Engineer
immutable: true

## Requirements
- R1: doc_analyzer reports a missing API key at runtime: the MCP stdio transport spawns
  sub-agent subprocesses with a minimal default environment, so GEMMA_API_KEY (and
  LANGSMITH_*) never reach them. SubAgentEndpoint.to_connection() must pass the parent
  process environment to stdio connections ("env" key); HTTP connections unchanged.

## Acceptance
- A1: to_connection() for a stdio endpoint includes env with GEMMA_API_KEY when set in
  the parent env (stub runtime); URL endpoints produce no env key; file compiles.
