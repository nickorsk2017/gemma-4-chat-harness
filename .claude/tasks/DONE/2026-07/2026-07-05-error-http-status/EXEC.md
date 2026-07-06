# EXEC — 2026-07-05-error-http-status

## v1 (implements PLAN v1; 7 files)
- chat_service.py: + GatewayValidationError(GatewayError); prompt/count/type/size checks
  raise it; upstream failures keep GatewayError (D1).
- routers/chat.py: _fail(status, text) -> JSONResponse with ApiResponse.fail body; both
  chat endpoints map 400/502/500; health untouched (D2).
- gateway/services/__init__.py: export GatewayValidationError.
- backend/CLAUDE.md rule 5 -> "Structured errors, honest status codes" (D3).
- chatService.ts: non-OK -> parse envelope, prefer error_text, fallback "HTTP <code>" (D4).
- chatStore.ts: error = thrown message when present (D5).
- tests: + non-OK envelope case; store error asserts exact message (D6).
