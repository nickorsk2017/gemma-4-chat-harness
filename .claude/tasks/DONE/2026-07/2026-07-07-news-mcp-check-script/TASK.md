# TASK — 2026-07-07-news-mcp-check-script
owner: Engineer
immutable: true

## Requirements
- R1: Script `mcp/scripts/news_check.py` that tests the news API over MCP.
- R2: Two modes:
  - `--via agent` (default): fastmcp stdio client spawns web_agent
    (`python -m web_agent.main`) and calls `get_news` directly — isolates the
    Tavily integration.
  - `--via orchestrator`: fastmcp streamable-HTTP client to the running mcp
    service (default http://localhost:8100/mcp, override --url) calls
    `orchestrate` with a news prompt — verifies the planner routes news to
    web_agent and returns a merged answer.
- R3: Loads TAVILY_API_KEY / GEMMA_API_KEY from repo-root .env (shell env wins);
  parses the AgentResponse envelope; exit 0 only on status=ok (agent mode also
  requires >=1 news item); readable output; --query/--limit flags.

## Acceptance
- A1: Both modes implemented, envelope parsed defensively (.data or JSON text).
- A2: Non-ok envelope or transport error -> stderr + exit 1.
