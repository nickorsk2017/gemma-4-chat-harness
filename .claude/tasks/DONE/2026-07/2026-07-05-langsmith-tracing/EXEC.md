# EXEC — 2026-07-05-langsmith-tracing

## v1
Implemented PLAN v1 exactly; config-only, no agent code touched.

1. docker-compose.yml (mcp service env): added LANGSMITH_TRACING (default false),
   LANGSMITH_API_KEY (default empty), LANGSMITH_ENDPOINT (default
   https://api.smith.langchain.com), LANGSMITH_PROJECT (default gemma-chat).
2. .env: appended real values (TRACING=true, key, endpoint, project=gemma-chat).
3. .env.example: appended optional LangSmith block, empty key, off by default.
4. mcp/.env.example: appended same block for local runs.

No dependency changes (langsmith ships with langchain-core; explicit in
master_orchestrator pyproject).
