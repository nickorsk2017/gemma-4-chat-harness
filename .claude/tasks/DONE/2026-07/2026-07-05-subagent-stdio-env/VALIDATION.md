# VALIDATION — 2026-07-05-subagent-stdio-env
## v1 — PASS
A1: AST-extracted to_connection unit test — stdio dict carries env with GEMMA_API_KEY and
PATH; url endpoint returns exactly {url, transport}; file compiles. Root cause (MCP stdio
default minimal env starving sub-agents of the key) no longer reachable.
