# VALIDATION — 2026-07-07-web-agent-tavily-search

## v1 — PASS
- A1 PASS: stubbed fastmcp.Client (asserts exact Tavily URL, tool name
  tavily_search, args {query,max_results,topic}): search_web maps 2 results into
  SearchResult; fetch_news maps into NewsItem with source=URL host; no LLM call
  in either path.
- A2 PASS: PLANNER_SYSTEM renders (double braces balance), contains search_web
  spec line and the mandatory news->web_agent rule.
- A3 PASS: without TAVILY_API_KEY providers raise RuntimeError; web_tools wraps
  all provider errors into AgentResponse.fail.
- Live Tavily call left to Engineer (sandbox has no egress): set TAVILY_API_KEY
  in .env, `make rebuild`, ask the agent for news.
