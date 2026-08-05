# TASK — 2026-07-07-news-check-ping-only
owner: Engineer
immutable: true

## Requirements
- R1: news_check.py must NOT invoke the orchestrator or any agent (no tools/call,
  no LLM work). It only pings the MCP API of the running service and reports
  whether it works.
- R2: Minimal code, stdlib only: (1) MCP handshake (initialize + initialized),
  (2) tools/list to confirm the API serves its tools, (3) print result, exit 0/1.

## Acceptance
- A1: No tools/call anywhere in the script.
- A2: Против живого MCP-подобного сервера: up -> prints server + tools, exit 0;
  down -> clear message, exit 1.
