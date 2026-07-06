# VALIDATION — 2026-07-05-error-http-status
## v1 — PASS
- A1 PASS (stub runtime through the real router+service code): success -> ApiResponse 200
  path; empty prompt / bad type / two files -> 400 with envelope error_text; orchestration
  failure -> 502; unexpected exception -> 500 "unexpected error".
- A2 PASS: tsc clean; chatService prefers envelope.error_text on non-OK with HTTP-code
  fallback (new jest case); store surfaces exact message (jest host-run, carried residual).
- A3 PASS: py_compile clean; backend/CLAUDE.md rule 5 documents 400/502/500 + envelope.
