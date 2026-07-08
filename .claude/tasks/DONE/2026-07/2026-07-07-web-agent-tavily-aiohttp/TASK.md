# TASK — 2026-07-07-web-agent-tavily-aiohttp
owner: Engineer
immutable: true

## Requirements
- R1: Move Tavily search/news logic into mcp/web_agent/providers/tavily.py using
  a direct aiohttp REST call to api.tavily.com/search (no hosted MCP client).
- R2: web_agent's tools use the new provider for live web data.
- R3: Delete the old Tavily-MCP logic and mcp/web_agent/tools/providers.py.

## Acceptance
- A1: providers/tavily.py returns SearchResult/NewsResult via aiohttp; config
  drives url/key/timeout. tools/providers.py gone; no fastmcp.Client / tavily_mcp refs.
- A2: web_tools imports from web_agent.providers; whole tree compiles.

## Constraints
- Keep non-Tavily providers (weather, page fetch) working (moved to providers/llm.py).
