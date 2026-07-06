# PLAN — 2026-07-05-langsmith-tracing

## v1

### Approach
LangSmith tracing is built into langchain-core/langgraph via the `langsmith` client and
is activated purely by environment variables. Every agent builds its model through
`agent_core.llm.build_chat_model` (LangChain `ChatOpenAI`), and the orchestrator's
LangGraph runs inherit the same process env; stdio sub-agent subprocesses receive the
parent env (established by task 2026-07-05-subagent-stdio-env, which explicitly
forwards LANGSMITH_*). Therefore: wire the four LANGSMITH_* vars into the mcp service
env and document them — zero agent code changes (satisfies R2).

### Changes (config only)
1. `docker-compose.yml` — mcp service `environment`: add
   `LANGSMITH_TRACING: "${LANGSMITH_TRACING:-false}"`,
   `LANGSMITH_API_KEY: "${LANGSMITH_API_KEY:-}"`,
   `LANGSMITH_ENDPOINT: "${LANGSMITH_ENDPOINT:-https://api.smith.langchain.com}"`,
   `LANGSMITH_PROJECT: "${LANGSMITH_PROJECT:-gemma-chat}"`.
   Defaults keep tracing OFF when unset (R3) — no `:?` requirement.
2. `.env` (gitignored) — add the real values supplied by the Engineer
   (TRACING=true, key, endpoint, project=gemma-chat).
3. `.env.example` — add a "LangSmith tracing" block: all four vars, empty key,
   comment that it covers ALL MCP agents and is optional.
4. `mcp/.env.example` — same block for local (non-docker) runs.

### Non-changes / rationale
- backend gateway and frontend make no LLM calls -> untouched.
- `langsmith` already a direct dep of master_orchestrator (>=0.8.16) and a transitive
  dep of langchain-core for every agent -> no dependency edits (A3).

### Validation plan
- `docker compose config` parses with and without LANGSMITH_* in the environment and
  shows the four vars on the mcp service (A1).
- `git check-ignore .env` confirms the secret file is untracked; grep tracked files
  for the key prefix `lsv2_` -> no hits (A2).
- `python -c "import langsmith"` inside mcp deps context or grep uv/pyproject (A3).
