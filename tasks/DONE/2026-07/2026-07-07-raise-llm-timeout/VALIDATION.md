# VALIDATION — 2026-07-07-raise-llm-timeout

## v1 — PASS
- A1 PASS: grep confirms LLM_REQUEST_TIMEOUT_S=90 and
  ORCHESTRATOR_SUBAGENT_TIMEOUT_S=200 in root .env (LLM line), docker-compose.yml
  defaults, and mcp/.env.example.
- A2 PASS: invariant 2x90=180 < 200 holds; no *.py changed; root .env diff was a
  single line (only the timeout), no stray backup files left, secrets intact.
- Live confirmation left to Engineer: `make up` (recreate mcp so new env applies)
  then re-run the PDF analysis — should no longer "Request timed out".
- Note: pure timeout raise; for very large PDFs that still exceed 90s, options A
  (truncate) / C (map-reduce) remain future work.
