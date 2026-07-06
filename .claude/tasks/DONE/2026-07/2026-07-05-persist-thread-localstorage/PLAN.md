# PLAN — 2026-07-05-persist-thread-localstorage

## v1

### Strategy
Persist the chat store's durable slice (R1, R2) with zustand's built-in `persist`
middleware (constraint: no new deps). Restore happens by store rehydration from
`localStorage`; `reset()` keeps clearing state and, because persisted writes follow
every `set`, the cleared state overwrites storage (R3). No service/backend changes (R4).

### SSR / hydration (A3)
Next.js pre-renders the client page; eager rehydration at module init would make the
client's first render differ from server HTML. Therefore: `skipHydration` on the
persist config, with explicit rehydration triggered from the chat feature after mount.
Expose a hydration flag from the store so the view knows when restore finished.

### Impact map
1. `frontend/stores/chatStore.ts` — wrap store creation with persist middleware:
   - storage key: `agent-chat`; JSON storage over `localStorage`.
   - partialize to `{ messages, threadId }` only (constraint: no transient state).
   - `skipHydration: true`; hydration flag set via the rehydrate callback.
2. `frontend/shared/features/chat/ChatView.tsx` — trigger rehydration in a mount
   effect; populate the "pre-existing message ids" set only once hydration completes,
   so restored assistant messages do not re-animate (typewriter stays for new replies
   only).
3. `frontend/__tests__/chatStore.test.ts` — extend:
   - after `send`, `localStorage["agent-chat"]` contains messages + threadId;
   - a fresh rehydrate restores them; `reset()` leaves storage empty-state (A2);
   - `beforeEach` clears `localStorage` so existing cases stay isolated.

### Risks
- Hydration mismatch if rehydration is eager → mitigated by skipHydration (step 1).
- Restored reply re-animating typewriter → mitigated in step 2.
- `localStorage` quota/corrupt JSON → persist middleware fails soft (store starts
  empty); acceptable for MVP scope.

### Sequencing
Step 1 → Step 2 → Step 3, then frontend `lint` + `test` (A4).
