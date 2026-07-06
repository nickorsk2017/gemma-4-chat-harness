# EXEC — 2026-07-05-typewriter-effect

## v1 (implements PLAN v1)

### Changes
1. NEW `frontend/shared/ui-kit/useTypewriter.ts` (PLAN S1)
   - `useTypewriter(text, enabled)` -> `{ visible, done }`.
   - setInterval @24ms; chars/tick derived from text length so total reveal is
     clamped to 0.4–4s; interval cleared on unmount/text change; `enabled=false`
     returns full text instantly.
2. MOD `frontend/shared/ui-kit/MessageBubble.tsx` (PLAN S2)
   - New optional props `animate` (default false) and `onTypingTick`.
   - Renders `visible` from the hook; blinking caret (`animate-pulse` span)
     while typing; effect fires `onTypingTick` as text grows.
3. MOD `frontend/shared/features/chat/ChatView.tsx` (PLAN S3)
   - `preexistingIds` ref captures ids present at first render -> those never
     animate (R3, incl. remount).
   - `animate` passed only when message is last AND role=assistant AND not
     preexisting (R3/R4).
   - `handleTypingTick` keeps scroll pinned to bottom during reveal (R5).

### Notes
- No backend/service/store changes (R2). No new deps. All files < 200 LOC.
