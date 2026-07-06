# PLAN — 2026-07-05-error-http-status

## v1
D1. chat_service.py: split exceptions — GatewayValidationError(GatewayError) raised by
    prompt/file checks; orchestration failure keeps GatewayError. (GatewayError stays the
    base so `except GatewayError` still catches both.)
D2. routers/chat.py: helper `_fail(status_code, text)` returning
    JSONResponse(status_code=..., content=ApiResponse.fail(text).model_dump(mode="json")).
    Both endpoints: GatewayValidationError -> 400; GatewayError -> 502; Exception -> 500.
    response_model stays for the 200 path.
D3. backend/CLAUDE.md rule 5: "Structured errors, honest status codes" — envelope always,
    400/502/500 mapping, never an unstructured 500.
D4. frontend chatService.ts: on !response.ok try response.json() -> envelope.error_text;
    throw ChatServiceError(error_text ?? `HTTP <status>`); keep envelope check on 200.
D5. chatStore.ts: catch (err) -> error = err instanceof Error && message ? message :
    generic fallback.
D6. Tests: chatService — non-OK with envelope surfaces error_text; non-OK without body
    falls back to HTTP code; chatStore — error shows thrown message.
Files (6): chat_service.py, routers/chat.py, backend/CLAUDE.md, chatService.ts,
chatStore.ts, __tests__ (2).
