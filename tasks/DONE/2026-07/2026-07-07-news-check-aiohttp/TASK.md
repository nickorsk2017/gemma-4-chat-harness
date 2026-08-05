# TASK — 2026-07-07-news-check-aiohttp
owner: Engineer
immutable: true

## Requirements
- R1: mcp/scripts/news_check.py makes a DIRECT request to Tavily's REST search
  API (https://api.tavily.com/search) using aiohttp — Bearer auth, JSON body
  {query, search_depth:"advanced"}. No agents, no orchestrator, no LLM.
- R2: TAVILY_API_KEY read from env or repo-root .env — never hardcoded.
- R3: Print numbered result titles + urls; exit 0 on results, 1 on error/no key.
- R4: Makefile news-check help line updated to reflect aiohttp/REST (was stdlib).

## Acceptance
- A1: Script imports aiohttp and POSTs only to api.tavily.com; py_compile clean.
- A2: no-key path -> stderr message + exit 1; results -> titles+urls + exit 0.

## Constraints
- aiohttp is the required HTTP client (Engineer directive).
