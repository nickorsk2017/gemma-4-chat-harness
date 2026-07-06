# PLAN — 2026-07-05-typewriter-effect

## v1

### Strategy
Backend delivers the full reply at once (R2), so the effect is a pure client-side
reveal animation: progressively grow the visible prefix of the assistant message
content on a timer until the full text is shown.

### Impact map
1. `frontend/shared/ui-kit/useTypewriter.ts` — NEW. Reusable hook: given (text,
   enabled) returns the currently visible slice + `done` flag. Interval-driven,
   reveals several chars per tick for smooth speed on long replies; cleans up on
   unmount; when disabled returns full text immediately. Pure presentation logic —
   ui-kit placement is legal (no store/service access).
2. `frontend/shared/ui-kit/MessageBubble.tsx` — MODIFY. New optional prop
   `animate?: boolean` (default false → R3/R4 safe by default). When set, content
   renders via the hook; optional blinking caret while typing. Stays presentational.
3. `frontend/shared/features/chat/ChatView.tsx` — MODIFY. Composition decides WHAT
   animates (R3/R4): pass `animate` only for the last message when it is an
   assistant message. Track "already animated" ids via a ref so a completed
   animation never replays on re-render. Extend the auto-scroll effect to also fire
   while typing progresses (R5) — simplest: MessageBubble accepts an optional
   `onTyping` callback or ChatView scrolls on an interval while last bubble
   animates; Executor picks the lighter variant that keeps files under RULE-A.

### Sequencing
S1 hook → S2 bubble prop → S3 ChatView wiring/scroll → S4 typecheck.

### Risks
- Re-animation on list re-render (R3): mitigated by animated-ids ref in ChatView
  and `animate=false` default.
- Timer leaks: hook must clear interval on unmount/text change.
- RULE-A: all touched files stay well under 200 LOC.

### Requirements coverage
R1→(1,2); R2→(strategy); R3,R4→(3); R5→(3); A3→(S4).
