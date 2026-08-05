# PLAN — 2026-07-07-web-agent-search-only

## v1
Shrink web_agent's surface to a single live-search tool.
- Delete providers/llm.py: weather/page tools are being dropped, and the LLM it
  wrapped is already available via agent_core.llm.get_llm() — no local copy needed.
- web_tools.py: keep only the search_web @mcp.tool (-> tavily.search_web); drop
  get_news/get_weather/fetch_url and their now-unused imports.
- providers/tavily.py: remove fetch_news (dead once get_news is gone) and its
  NewsItem/NewsResult/urlparse imports; search_web stays.
- config.py: fix the doc comment referencing get_news.
Schemas (schemas/web.py, schemas/http.py) left intact — harmless contracts.
