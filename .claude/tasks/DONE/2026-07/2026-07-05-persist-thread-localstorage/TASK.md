# TASK — 2026-07-05-persist-thread-localstorage
owner: Engineer
immutable: true

## Requirements
- R1: `threadId` must persist in `localStorage` so a page reload continues the same server-side conversation thread.
- R2: Chat messages must persist in `localStorage` and be restored on page reload (chat shows old messages).
- R3: `reset()` must clear the persisted state (new thread + empty chat after reset, including after reload).
- R4: Frontend-only change (Engineer decision): no gateway/orchestrator changes; restore source is localStorage, not a server history endpoint.

## Acceptance
- A1: Send a message, reload the page -> old messages are rendered and the next message is sent with the same `thread_id`.
- A2: After `reset()` + reload -> empty chat, no `thread_id` sent on the next first message.
- A3: No SSR hydration errors/warnings in the Next.js app (store hydrates safely on the client).
- A4: `npm test` and `npm run lint` in `frontend/` pass; existing chatStore tests updated as needed.

## Constraints
- Zustand `persist` middleware (already available via the pinned `zustand` package); no new dependencies.
- Do not persist transient state (`isSending`, `error`).
- Respect frontend layer rules (store delegates HTTP to services; ui-kit untouched).
