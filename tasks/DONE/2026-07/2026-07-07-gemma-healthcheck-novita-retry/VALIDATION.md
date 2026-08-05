# VALIDATION — 2026-07-07-gemma-healthcheck-novita-retry

## v1 — PASS
- A1 PASS: stub run exercised both paths — 4 failing attempts -> exit 1 with
  per-attempt stderr lines; passing stub -> answer + exit 0.
- A2 PASS: provider/model/messages/temperature/.env loader untouched (diff is
  retry loop + max_tokens only).
- Live Novita call left to Engineer.
