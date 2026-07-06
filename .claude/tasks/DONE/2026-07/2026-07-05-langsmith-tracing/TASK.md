# TASK — 2026-07-05-langsmith-tracing
owner: Engineer
immutable: true

## Requirements
- R1: All MCP AI agents (master_orchestrator planner/graph + web_agent, doc_analyzer,
  image_analyzer sub-agents) send LangChain/LangGraph traces to LangSmith,
  project "gemma-chat".
- R2: Use the standard LANGSMITH_* env vars (LANGSMITH_TRACING, LANGSMITH_API_KEY,
  LANGSMITH_ENDPOINT, LANGSMITH_PROJECT) consumed natively by langchain-core/langsmith —
  no agent code changes.
- R3: Composed stack: docker-compose mcp service forwards the four vars from host .env.
  Tracing must be optional — stack boots with tracing off when vars are unset.
- R4: Local runs: .env carries the real values (gitignored); .env.example and
  mcp/.env.example document the block with an empty key.

## Acceptance
- A1: `docker compose config` succeeds with and without LANGSMITH_* set; mcp service
  env contains the four vars.
- A2: .env has the provided key/endpoint/project; no secret appears in any tracked file.
- A3: langsmith package is available to every agent (dependency of langchain-core;
  already explicit in master_orchestrator).

## Constraints
- No changes to agent code or backend/frontend services (gateway makes no LLM calls).
- Secrets only in gitignored .env.
