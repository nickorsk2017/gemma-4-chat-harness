# EXEC — 2026-07-07-news-check-ssl-certifi

## v1
Import certifi (optional; _CAFILE=certifi.where() or None). In _search build
ssl.create_default_context(cafile=_CAFILE) and pass it via
aiohttp.TCPConnector(ssl=ctx) to ClientSession. Fixes macOS
CERTIFICATE_VERIFY_FAILED. 1 file (news_check.py).
