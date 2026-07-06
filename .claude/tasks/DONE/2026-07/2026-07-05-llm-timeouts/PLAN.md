# PLAN — 2026-07-05-llm-timeouts
## v1
D1. backend/_common/env/settings.py: orchestrator_timeout_s 30.0 -> 180.0 (comment: must
    exceed planner + slowest sub-agent + synthesis).
D2. mcp/master_orchestrator/config.py: subagent_timeout_s 30.0 -> 120.0.
D3. docker-compose.yml: backend env GATEWAY_ORCHESTRATOR_TIMEOUT_S "180"; mcp env
    ORCHESTRATOR_SUBAGENT_TIMEOUT_S "120" (explicit, overridable via .env).
D4. mcp/.env.example: ORCHESTRATOR_SUBAGENT_TIMEOUT_S=120.
Files (4).
