# TASK — 2026-07-07-news-check-ssl-certifi
owner: Engineer
immutable: true

## Requirements
- R1: news_check.py must verify TLS against a working CA bundle so the Tavily
  HTTPS call succeeds on hosts whose Python lacks system CA certs (macOS
  python.org / Homebrew): SSLCertVerificationError.
## Acceptance
- A1: aiohttp uses an ssl context built from certifi's CA bundle when certifi is
  present; graceful fallback to system trust store when it is absent. py_compile clean.
