# PLAN — 2026-07-07-web-agent-tavily-search

## v1
Client: web_agent already depends on fastmcp; use `fastmcp.Client(<url>)`
(streamable-HTTP) per call — stateless, no long-lived connection to manage in
the stdio sub-agent. Tavily's MCP exposes `tavily_search` (args: query,
max_results, topic and others; JSON text content with `results:[{title,url,content}]`).

Changes:
1. web_agent/config.py: `tavily_api_key` (env TAVILY_API_KEY),
   `tavily_mcp_base` (env WEB_AGENT_TAVILY_MCP_BASE, default
   https://mcp.tavily.com/mcp/), helper `tavily_mcp_url()` -> base?tavilyApiKey=key.
2. schemas/web.py: SearchItem{title,url,content}, SearchResult{query,results}.
3. schemas/http.py: SearchRequest{query, max_results 1-10 default 5},
   SearchResponse alias.
4. tools/providers.py: `_tavily_results(query, max_results, topic)` — RuntimeError
   if no key; Client(url) -> call_tool("tavily_search", ...); parse first text
   block as JSON, tolerate structured `.data`. `search_web()` (topic general),
   `fetch_news()` -> topic news, map into NewsItem (source = URL host,
   summary = content snippet). Weather/fetch_url stay LLM-backed (out of scope).
   Drop now-unused NEWS_GEN import.
5. tools/web_tools.py: register `search_web` tool (docstring says: live internet
   search — news, current events, fresh facts).
6. master_orchestrator/prompts/orchestrate.py: add search_web arg-spec line
   (double-braced) + routing rule: news/current-events prompts MUST create a
   web_agent sub-task (get_news for news; search_web for other live facts).
7. docker-compose.yml: mcp env TAVILY_API_KEY: "${TAVILY_API_KEY:-}".
8. .env.example: TAVILY_API_KEY entry.

Risks: Tavily result JSON shape drift -> defensive .get() mapping; empty key ->
tool returns AgentResponse.fail via existing except in web_tools (A3 holds since
providers raise RuntimeError).
