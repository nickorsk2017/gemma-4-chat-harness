# PLAN — 2026-07-04-connect-chat-rest

## v1

### Approach
Swap the mock body of `sendChatMessage` for a real `fetch` against the gateway,
parsing the shared `ApiResponse` envelope. Signature stays identical (R3), so
`stores/chatStore.ts` and all components are untouched.

### Files
1. `frontend/services/chatService.ts` — rewrite:
   - `API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"` (module const; NEXT_PUBLIC_* is inlined at build time).
   - `POST ${API_BASE_URL}/api/chat`, JSON body `{prompt}` (matches `ChatRequest`; `context` is optional server-side).
   - Pass `signal` to fetch (abort works natively).
   - Non-OK HTTP -> throw `ChatServiceError`.
   - Parse envelope `{status, data, error_text}`; `status !== "Success"` or missing `data.reply` -> throw `ChatServiceError(error_text)`.
   - Return `{reply: data.reply}` (`SendMessageResponse`).
2. `frontend/__tests__/chatService.test.ts` — rewrite: stub `global.fetch`;
   cases: success envelope -> reply; Failed envelope -> throws with error_text;
   HTTP 500 -> throws; aborted signal -> rejects; correct URL/method/body sent.
3. `frontend/.env.local.example` — new: document `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`.

### Non-changes
- `types/chat.d.ts` stays (envelope type declared locally in the service — it is
  the network boundary's private wire format).
- Backend untouched: contract already matches, CORS already allows :3000.

### Risks
- Jest env lacks `fetch` on old Node — tests stub `global.fetch` explicitly, so no dependency on runtime fetch.
