# TASK — 2026-07-07-web-agent-tavily-search
owner: Engineer
immutable: true

## Requirements
- R1: Add real internet search to web_agent via Tavily's hosted MCP endpoint
  `https://mcp.tavily.com/mcp/?tavilyApiKey=<TAVILY_API_KEY>`.
- R2: New MCP tool `search_web` on web_agent (live search).
- R3: News questions must route to web_agent and hit Tavily: back the existing
  `get_news` tool with Tavily (topic=news) instead of the LLM-imagination prompt,
  and teach the planner that news/current-events prompts go to web_agent.
- R4: Key from env `TAVILY_API_KEY`; wire through docker-compose into the mcp
  service; document in .env.example.

## Acceptance
- A1: `search_web` and `get_news` call Tavily MCP and map results into pydantic
  schemas (no LLM in the news path).
- A2: Planner prompt lists search_web and mandates web_agent for news.
- A3: Missing TAVILY_API_KEY -> clean AgentResponse.fail, not a crash.
