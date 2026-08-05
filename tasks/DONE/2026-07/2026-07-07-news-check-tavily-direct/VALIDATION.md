# VALIDATION — 2026-07-07-news-check-tavily-direct

## v1 — PASS
- A1 PASS: grep -i "orchestrate|web_agent|openai|8100" -> zero matches; only
  mcp.tavily.com is contacted; stdlib imports only; py_compile OK.
- A2 PASS: stub-server run (below) prints results exit 0; no-key path exits 1
  with message; unreachable host exits 1.
- Live call to mcp.tavily.com left to Engineer (sandbox has no egress):
  `make news-check`.
