# TASK — 2026-07-07-news-check-stdlib
owner: Engineer
immutable: true

## Requirements
- R1: news_check.py must run with NO docker and NO project deps — pure Python
  stdlib — and only verify the RUNNING mcp service (default
  http://localhost:8100/mcp, --url override).
- R2: Speak MCP streamable-HTTP directly: initialize -> notifications/initialized
  -> tools/call orchestrate (news prompt); parse SSE or JSON responses; verify
  envelope status=ok and that web_agent handled the news sub-task.
- R3: Makefile news-check target runs it host-side ($(PYTHON), no compose);
  README line updated. Clear message + exit 1 when the service is down.

## Acceptance
- A1: `python3 mcp/scripts/news_check.py` works with stdlib only (no imports
  beyond stdlib).
- A2: `make news-check` no longer uses docker.
- A3: ok / misroute / service-down paths behave (0 / 1 / 1 + hint).
