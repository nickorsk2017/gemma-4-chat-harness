# TASK — 2026-07-05-typewriter-effect
owner: Engineer
immutable: true

## Requirements
- R1: Assistant replies in the chat render with a ChatGPT-style typewriter effect (text appears character by character).
- R2: Frontend-only implementation; no backend/gateway/MCP changes. Backend still returns the full reply in one response.
- R3: Only the newly arrived assistant message animates; previously rendered history renders instantly (no re-animation on re-render).
- R4: User messages and error banners never animate.
- R5: Auto-scroll keeps following the bottom while text is being typed.

## Acceptance
- A1: Sending a prompt shows the reply typing out progressively at a smooth, readable speed.
- A2: Older messages appear instantly when the list re-renders.
- A3: `npx tsc --noEmit` passes; frontend layering rules (RULE-A <=200 LOC, RULE-B ui-kit) hold.

## Constraints
- Respect frontend layer boundaries: ui-kit stays presentational (no store/service access).
- No new runtime dependencies.
