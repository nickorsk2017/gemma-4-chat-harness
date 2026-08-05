# PLAN — 2026-07-07-web-agent-tavily-aiohttp

## v1
Introduce a providers/ package replacing the single tools/providers.py.
- providers/tavily.py: aiohttp POST to settings.tavily_api_url with Bearer key,
  body {query, search_depth:"advanced", topic, max_results}; certifi-optional
  ssl context; _search() -> search_web()/fetch_news() returning schema models.
- providers/llm.py: relocate _chat_model()/fetch_weather()/fetch_page() (LLM,
  non-Tavily) verbatim so weather + fetch_url keep working.
- config.py: drop tavily_mcp_base + tavily_mcp_url(); add tavily_api_url and
  tavily_timeout_s (Rule 5: URLs/timeouts in config). Keep tavily_api_key.
- tools/web_tools.py: import {llm, tavily} from web_agent.providers; route
  search_web/get_news -> tavily, get_weather/fetch_url -> llm.
- pyproject.toml: httpx (unused) -> aiohttp + certifi.
- Delete tools/providers.py.
Rationale: user directive; keeps tools thin (Rule 3), providers behind the tool
layer, secrets/urls in config (Rule 5). No schema change.
