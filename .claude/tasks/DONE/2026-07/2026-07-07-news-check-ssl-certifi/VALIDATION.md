# VALIDATION — 2026-07-07-news-check-ssl-certifi
validation_version: 1
result: PASS

## v1 — PASS
- A1 PASS: py_compile clean; certifi import is optional with fallback; ssl
  context passed through TCPConnector. Live `make news-check` on the host (with
  certifi installed) resolves the CERTIFICATE_VERIFY_FAILED error.
