# VALIDATION — 2026-07-07-gemma-healthcheck-novita

## v1 — PASS
- A1 PASS: stubbed openai run asserts base_url/model/messages/max_tokens/
  temperature; real Novita key (sk_...) picked up from repo .env; answer printed,
  exit 0.
- A2 PASS: failure path exits 1 with [gemma-check] FAILED on stderr (exercised
  by stub assert on first run).
- Live Novita call left to Engineer (no egress in sandbox).
