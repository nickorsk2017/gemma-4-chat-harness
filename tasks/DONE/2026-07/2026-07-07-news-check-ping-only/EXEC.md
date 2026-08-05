# EXEC — 2026-07-07-news-check-ping-only

## v1
news_check.py rewritten to a ~70-line stdlib MCP ping: initialize (+session id)
-> initialized notification -> tools/list; prints server name/version + tool
names; URLError -> "MCP DOWN ... make up" exit 1, other errors -> "MCP BROKEN"
exit 1. No tools/call, no orchestrator/agent invocation. Makefile target
unchanged (still `$(PYTHON) mcp/scripts/news_check.py`).
