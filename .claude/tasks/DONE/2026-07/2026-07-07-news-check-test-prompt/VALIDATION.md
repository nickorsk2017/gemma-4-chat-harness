# VALIDATION — 2026-07-07-news-check-test-prompt

## v1 — PASS
- A1 PASS: fake server asserts prompt == "What is the last news?"; answer text
  printed verbatim.
- A2 PASS: ok -> exit 0; error envelope -> "FAILED — boom" exit 1; down ->
  "MCP DOWN ... make up" exit 1. py_compile OK; stdlib only.
- Live run vs real stack left to Engineer: `make news-check`.
