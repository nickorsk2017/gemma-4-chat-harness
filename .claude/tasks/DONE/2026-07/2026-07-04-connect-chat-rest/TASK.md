# TASK — 2026-07-04-connect-chat-rest
owner: Engineer
immutable: true

## Requirements
- R1: Replace the mock in `frontend/services/chatService.ts` with a real `fetch` to the gateway `POST /api/chat` (envelope `ApiResponse[ChatReply]`: `{status: "Success"|"Failed", data?, error_text?}`).
- R2: Gateway base URL configurable via `NEXT_PUBLIC_API_BASE_URL` (default `http://localhost:8000`); no hardcoded URLs in the service body.
- R3: Keep the `sendChatMessage(request, signal?)` signature stable — no changes required in `stores/` or components.
- R4: On `status: "Failed"` or non-OK HTTP, throw so the store's existing catch path shows its error message. AbortSignal must still cancel the request.
- R5: Update `frontend/__tests__/chatService.test.ts` to mock `fetch` (no live network in tests).

## Acceptance
- A1: `npm test` passes in `frontend/`.
- A2: With the gateway on :8000 and `npm run dev`, a message typed on /chat renders a real reply from `/api/chat` (mock orchestrator mode is fine).
- A3: Failed envelope / network error surfaces the store's error string; UI does not crash.

## Constraints
- services/ remains the single network boundary (frontend/CLAUDE.md layers).
- No new runtime dependencies.
