# EXEC — 2026-07-04-connect-chat-rest

## v1
Per PLAN v1:
1. `frontend/services/chatService.ts` — mock removed; real `fetch` POST `${API_BASE_URL}/api/chat`
   (`API_BASE_URL` = `NEXT_PUBLIC_API_BASE_URL` ?? `http://localhost:8000`). Local `ApiResponse`/`ChatReply`
   wire types; `ChatServiceError` exported; non-OK HTTP, Failed envelope, and missing `data.reply` all throw;
   `signal` forwarded to fetch. Public signature unchanged (R1–R4).
2. `frontend/__tests__/chatService.test.ts` — rewritten with `global.fetch` stub: success, Failed envelope,
   empty data, HTTP 500, abort-signal cases (R5).
3. `frontend/.env.local.example` — added, documents `NEXT_PUBLIC_API_BASE_URL`.
No changes to stores/, components, types/, or backend.
