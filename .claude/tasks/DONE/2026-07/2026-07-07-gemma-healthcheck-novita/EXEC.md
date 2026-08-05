# EXEC — 2026-07-07-gemma-healthcheck-novita

## v1
`mcp/scripts/gemma_healthcheck.py`: Engineer snippet verbatim (openai SDK,
base_url https://api.novita.ai/openai, google/gemma-4-31b-it, system+user,
max_tokens=131072, temperature=0.7); key from env GEMMA_API_KEY via root-.env
loader (R2); try/except -> stderr + exit 1 (A2). py_compile OK.
