# TASK — 2026-07-07-news-check-test-prompt
owner: Engineer
immutable: true

## Requirements
- R1: news_check.py must send the test prompt "What is the last news?" to the
  running MCP service (tools/call orchestrate) and print the returned answer.
- R2: Keep it minimal and stdlib-only: handshake -> one tools/call -> print
  answer; exit 0 on ok answer, 1 on error/down.

## Acceptance
- A1: Script sends exactly the prompt "What is the last news?" and prints the
  answer text from the envelope.
- A2: up/ok -> exit 0; error envelope / service down -> exit 1 with message.
