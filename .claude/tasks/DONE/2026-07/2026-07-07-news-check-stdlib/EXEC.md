# EXEC — 2026-07-07-news-check-stdlib

## v1
Rewrote mcp/scripts/news_check.py per PLAN v1: stdlib-only (argparse/json/sys/
urllib) MCP streamable-HTTP client — initialize (captures mcp-session-id) ->
notifications/initialized -> tools/call orchestrate; SSE and plain-JSON body
parsing; envelope from structuredContent with content[0].text fallback; checks
status=ok + web_agent among sub-task results; URLError -> "Is the stack
running? Try: make up". Makefile news-check -> `@$(PYTHON)
mcp/scripts/news_check.py $(ARGS)` (no compose); README line reworded. 3 files.
