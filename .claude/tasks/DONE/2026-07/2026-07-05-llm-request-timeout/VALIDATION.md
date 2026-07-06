# VALIDATION — 2026-07-05-llm-request-timeout
## v1 — PASS
A1: stub runtime — ChatOpenAI receives timeout=90 (default) / 45 (env override) and
max_retries=1 for both providers; compiles. Hanging endpoint now fails fast inside the
sub-agent budget with a clear httpx timeout error instead of a bare budget timeout.
