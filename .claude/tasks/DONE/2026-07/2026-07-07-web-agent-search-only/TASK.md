# TASK — 2026-07-07-web-agent-search-only
owner: Engineer
immutable: true

## Requirements
- R1: Delete mcp/web_agent/providers/llm.py — redundant with agent_core
  (get_llm/build_chat_model already provide the shared model).
- R2: mcp/web_agent/tools/web_tools.py exposes exactly one tool: search_web.

## Acceptance
- A1: providers/llm.py gone; no build_chat_model/fetch_weather/fetch_page refs
  in web_agent.
- A2: web_tools registers only search_web (-> tavily.search_web); tree compiles.

## Constraints
- Remove now-dead fetch_news from providers/tavily.py (its get_news tool is gone).
