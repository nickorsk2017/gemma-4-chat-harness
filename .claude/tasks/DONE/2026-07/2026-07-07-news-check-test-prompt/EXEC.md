# EXEC — 2026-07-07-news-check-test-prompt

## v1
news_check.py: kept the minimal stdlib handshake, added one tools/call
`orchestrate` with the fixed prompt "What is the last news?" (thread news-check,
--timeout 240 default); envelope from structuredContent (text fallback); prints
the answer; exit 0 only on status=ok + non-empty answer. Single file.
