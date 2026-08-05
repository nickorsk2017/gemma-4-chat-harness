# PLAN — 2026-07-07-news-check-stdlib

## v1
MCP streamable-HTTP is plain JSON-RPC over POST with SSE-or-JSON responses —
implementable with urllib.request:
1. POST initialize (protocolVersion 2025-03-26, clientInfo news_check);
   capture `mcp-session-id` response header.
2. POST notifications/initialized with the session header (202, no body).
3. POST tools/call {name: orchestrate, arguments: {request: {prompt, thread_id:
   news-check}}}; long read timeout (--timeout, default 240s = gateway budget).
Response parsing: Content-Type json -> json.loads; text/event-stream -> collect
`data:` lines, take the last JSON-RPC message with our id. Tool payload:
result.structuredContent, falling back to json.loads(result.content[0].text).
Checks (same semantics as before): envelope.status == ok, answer printed,
web_agent present among data.results agents -> exit 0; otherwise exit 1.
URLError/ConnectionRefused -> "service is not running — make up" + exit 1.
Makefile: `$(PYTHON) mcp/scripts/news_check.py $(ARGS)`; README line reworded.
Rewrite the script wholesale (old stdio/fastmcp modes die — they contradict R1).
