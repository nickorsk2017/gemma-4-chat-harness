# EXEC — 2026-07-05-web-agent-gemma-llm

## v1 (implements PLAN v2)
- web_agent/prompts/generate.py (new): NEWS_GEN / WEATHER_GEN / PAGE_GEN, honest
  "model cannot browse, flag uncertainty" framing (D1).
- web_agent/tools/providers.py: rewritten — `_llm_ready()` gate (llm_provider != mock and
  llm_api_key set), cached `_chat_model()` via agent_core build_chat_model
  (nvidia/gemma/base_url from settings), each provider real path =
  `with_structured_output(Schema).ainvoke(prompt)`; mock branches byte-identical (D2).
- web_agent/pyproject.toml: + langchain-core>=0.3.0 (providers now import BaseChatModel
  type directly) — deviation from D3 (justified: direct import for the cache type hint).
- Alias rename NVIDIA_API_KEY -> GEMMA_API_KEY in all 4 configs + agent_core/llm.py
  docstring (D5).
- .gitignore: ignore .env / .env.* except .env.example; .env.example documents
  GEMMA_API_KEY (D4).
- Environment provisioning (not tracked): local .env written with the user's real
  GEMMA_API_KEY, mode 0600; confirmed gitignored.
