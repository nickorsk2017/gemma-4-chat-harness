# EXEC — 2026-07-05-llm-timeout-budgets

## v1
Per PLAN v1, env-only:
1. docker-compose.yml mcp env: + LLM_REQUEST_TIMEOUT_S (default 45).
2. .env: LLM_REQUEST_TIMEOUT_S=45, GATEWAY_ORCHESTRATOR_TIMEOUT_S=240.
3. .env.example: documented both; mcp/.env.example: documented LLM_REQUEST_TIMEOUT_S.
No code changes.
