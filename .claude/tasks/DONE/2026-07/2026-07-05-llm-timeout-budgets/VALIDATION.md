# VALIDATION — 2026-07-05-llm-timeout-budgets

## v1 — PASS
- A1 PASS: compose parses; mcp env LLM_REQUEST_TIMEOUT_S="${LLM_REQUEST_TIMEOUT_S:-45}".
- A2 PASS: .env sets 45/240; both examples document the knobs.
- A3 PASS: 2*45=90 < 120 sub-agent budget; gateway 240 > plan(<=90)+dispatch(<=120)
  typical path; worst case documented in PLAN. Env-only, 4 files, matches PLAN v1.
