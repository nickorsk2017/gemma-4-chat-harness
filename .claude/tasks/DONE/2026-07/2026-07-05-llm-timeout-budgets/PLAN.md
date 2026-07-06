# PLAN — 2026-07-05-llm-timeout-budgets

## v1

### Diagnosis (from LangSmith trace + code)
agent_core.llm sets per-request timeout 90s with max_retries=1. Sub-agent budget is
120s. A single hung HTTP attempt (observed on summarize_document) burns 90s, leaving
30s for the retry that typically needs ~30s -> races the cap; trace died at 122s.
Normal gemma latency is 6-31s, so 45s per attempt is ample: hang + retry = <=90s < 120s.

### Changes (env-only)
1. docker-compose.yml, mcp service env: add
   `LLM_REQUEST_TIMEOUT_S: "${LLM_REQUEST_TIMEOUT_S:-45}"` (read by
   agent_core.llm._request_timeout(), inherited by stdio sub-agents).
2. .env: `LLM_REQUEST_TIMEOUT_S=45`, `GATEWAY_ORCHESTRATOR_TIMEOUT_S=240`
   (compose already forwards the gateway var; 240 covers plan<=90 + dispatch<=120 +
   synth typical <=31 with slack; absolute worst case 300 is accepted — sub-agent
   failures degrade gracefully into a synthesized answer, as observed).
3. .env.example + mcp/.env.example: document both knobs next to the existing
   timeout entries.

### Validation plan
- compose parses; mcp env carries LLM_REQUEST_TIMEOUT_S with default 45 (A1).
- .env / examples updated (A2); arithmetic: 2*45=90 < 120 (A3).
