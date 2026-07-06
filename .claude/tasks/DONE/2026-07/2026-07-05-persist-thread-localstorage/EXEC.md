# EXEC — 2026-07-05-persist-thread-localstorage

## v1 (implements PLAN v1)

### Changes
1. `frontend/stores/chatStore.ts`
   - Store wrapped in `persist(createJSONStorage(() => localStorage))`,
     key `agent-chat` (exported as `CHAT_STORAGE_KEY`).
   - `partialize` -> `{ messages, threadId }` only (R1, R2; transient state excluded).
   - `skipHydration: true`; new `hydrated` flag set from `onRehydrateStorage` (A3).
   - `send`/`reset` logic unchanged; `reset()` now also overwrites the persisted
     slice via the middleware's write-through (R3).
2. `frontend/shared/features/chat/ChatView.tsx`
   - Mount effect calls `useChatStore.persist.rehydrate()` (client-only restore).
   - Pre-existing-ids snapshot now waits for `hydrated` so restored assistant
     messages do not re-run the typewriter.
3. `frontend/__tests__/chatStore.test.ts`
   - `localStorage.clear()` added to setup; new suite "chatStore persistence":
     persists slice, restores on rehydrate, same thread_id after reload,
     reset clears storage (A1, A2).

### Verification runs (sandbox)
- `npx tsc --noEmit` -> clean (exit 0).
- Behavior harness (node, compiled store + service stub + localStorage stub,
  simulated reloads via fresh module instances): send -> persist -> reload ->
  restore -> same `thread_id` -> reset -> empty; ALL CHECKS PASSED.
- `jest` / `next lint` could NOT run in the sandbox: pnpm `node_modules` were
  installed on macOS; the Next.js SWC binary for linux/arm64 is absent and the
  npm registry is unreachable from the sandbox. Not a code defect — flagged for
  the Validator; A4 to be re-confirmed on the host (`npm test`, `npm run lint`).
