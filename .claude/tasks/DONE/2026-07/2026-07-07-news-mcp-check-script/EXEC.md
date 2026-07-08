# EXEC — 2026-07-07-news-mcp-check-script

## v1
Created mcp/scripts/news_check.py (single file): argparse (--via agent|
orchestrator, --query, --limit, --url); root-.env loader for TAVILY/GEMMA keys;
_envelope() parses CallToolResult .data with JSON-text fallback; agent mode —
StdioTransport spawns web_agent, calls get_news, prints items, fails on
status!=ok or 0 items; orchestrator mode — HTTP client, orchestrate with news
prompt, prints sub-agents + answer, fails if web_agent absent from results.
py_compile OK.
