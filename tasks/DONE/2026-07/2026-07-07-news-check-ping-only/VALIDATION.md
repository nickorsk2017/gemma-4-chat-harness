# VALIDATION — 2026-07-07-news-check-ping-only

## v1 — PASS
- A1 PASS: grep "tools/call" -> zero matches; only initialize/initialized/
  tools/list JSON-RPC methods used.
- A2 PASS: vs local MCP-shaped server (SSE + session header asserted):
  up -> "MCP OK — master_orchestrator v0.1.0", tools listed, exit 0;
  down -> "MCP DOWN ... Try: make up", exit 1. py_compile OK; stdlib only.
