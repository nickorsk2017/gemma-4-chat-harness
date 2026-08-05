# EXEC — 2026-07-07-web-agent-tavily-search

## v1
Per PLAN v1, 8 files:
1. web_agent/config.py — tavily_api_key (TAVILY_API_KEY), tavily_mcp_base,
   tavily_mcp_url().
2. web_agent/schemas/web.py — SearchItem, SearchResult.
3. web_agent/schemas/http.py — SearchRequest (max_results 1-10), SearchResponse.
4. web_agent/tools/providers.py — _tavily_results() via fastmcp.Client (structured
   .data first, JSON-text fallback, defensive mapping); search_web(topic=general);
   fetch_news -> Tavily topic=news (LLM prompt path removed); weather/page intact.
5. web_agent/tools/web_tools.py — new search_web tool, envelope-fail on exception.
6. master_orchestrator/prompts/orchestrate.py — search_web arg-spec + news
   routing rule (news/current events MUST -> web_agent get_news; other live
   facts -> search_web).
7. docker-compose.yml — TAVILY_API_KEY passthrough to mcp service.
8. .env.example — TAVILY_API_KEY documented.
py_compile OK on all six Python files.
