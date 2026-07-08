# VALIDATION — 2026-07-07-news-check-stdlib

## v1 — PASS
- A1 PASS: AST check — imports are argparse/json/sys/urllib/__future__ only;
  py_compile OK.
- A2 PASS: `make -n news-check` -> `python3 mcp/scripts/news_check.py` (no docker).
- A3 PASS: exercised against a local fake MCP server speaking streamable-HTTP
  (SSE bodies, session-id header asserted): ok -> exit 0; error envelope ->
  exit 1; misroute (no web_agent) -> exit 1; server down -> exit 1 with
  make-up hint.
- Live run against the real stack left to Engineer: `make news-check`.
