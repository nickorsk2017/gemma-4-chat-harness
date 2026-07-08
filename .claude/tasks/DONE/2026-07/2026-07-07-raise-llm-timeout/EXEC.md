# EXEC — 2026-07-07-raise-llm-timeout

## v1
- root .env: LLM_REQUEST_TIMEOUT_S 45 -> 90 (sed on line 22 only; single-line
  diff verified; secrets untouched; temp backup removed).
- docker-compose.yml: ORCHESTRATOR_SUBAGENT_TIMEOUT_S default 120 -> 200;
  LLM_REQUEST_TIMEOUT_S default 45 -> 90; comment updated (2x90s within 200s).
- mcp/.env.example: ORCHESTRATOR_SUBAGENT_TIMEOUT_S 120 -> 200;
  LLM_REQUEST_TIMEOUT_S 45 -> 90.
No Python changed.
