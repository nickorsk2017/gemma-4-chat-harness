# EXEC — 2026-07-07-agent-core-novita

## v1
`mcp/agent_core/llm.py` rewritten: NOVITA_BASE_URL https://api.novita.ai/openai,
key GEMMA_API_KEY only, DEFAULT_MODEL google/gemma-4-31b-it (GEMMA_MODEL env
override), dropped OpenRouter reasoning extra_body (R2); ChatOpenAI + timeout +
max_retries=1 + temp 0.5 kept; public surface unchanged (R3). py_compile OK.
