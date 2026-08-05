# EXEC — 2026-07-07-gemma-healthcheck-novita-retry

## v1
`mcp/scripts/gemma_healthcheck.py`: wrapped the call in a 4-attempt loop with
2/4/8s backoff (R2); max_tokens 131072 -> 512 (R3); success -> stdout + exit 0,
attempt progress + final failure -> stderr + exit 1. Nothing else changed (A2).
