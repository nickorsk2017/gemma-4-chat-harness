# TASK — 2026-07-07-news-check-tavily-direct
owner: Engineer
immutable: true

## Requirements
- R1: news_check.py: NO agents, NO orchestrator, NO LLM. Only a direct test call
  to the Tavily MCP server (https://mcp.tavily.com/mcp/?tavilyApiKey=<key>) and
  the result.
- R2: The Engineer-supplied OpenAI Responses snippet cannot run here (needs
  OPENAI_API_KEY + gpt-4.1 = an LLM deciding to call the tool); implement the
  equivalent without the model: MCP handshake -> tools/call tavily_search with
  the test query "What is the last news?" -> print results.
- R3: Stdlib only; TAVILY_API_KEY from env or repo-root .env; exit 0 on results,
  1 on error. Makefile/README help lines updated.

## Acceptance
- A1: Script talks only to mcp.tavily.com; grep clean of orchestrate/web_agent/openai/8100.
- A2: ok -> titles+urls printed, exit 0; error/no key/unreachable -> message, exit 1.
