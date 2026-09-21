# TASK — 2026-09-21-style-chat-ui
owner: Engineer
immutable: true

## Requirements
- R1: Restyle the chat UI to match the supplied reference mockup: the chat is a centered
  rounded card floating on a light neutral page background, with a soft outer shadow and
  a hairline border.
- R2: Header — product title "Gemma 4" followed by a small rounded "Chat" pill in the
  accent color; the subtitle line stays below it; the reset action is a rounded pill
  button with a refresh glyph and the label "Reset chat" on the right.
- R3: Message rows carry a circular avatar: assistant on the left with a four-point
  star glyph on a tinted accent circle, user on the right with a neutral person glyph.
  A timestamp in small muted text sits under each bubble, aligned to the bubble side.
- R4: Bubbles — user bubble solid accent with white semibold text, assistant bubble light
  neutral with dark text; both fully rounded (no tail notch), generous padding.
- R5: Composer — a full-width rounded pill text field, a circular outlined attach button
  with a paperclip glyph on the left, and a square rounded accent send button with a
  paper-plane glyph on the right (no "Send" word).
- R6: Empty state and status states (agent typing, error, attachment warning) restyled
  to the same visual language.
- R7: Color, radius, shadow and surface values are defined once as CSS custom properties
  in `app/globals.css` and consumed by the components; both light and dark schemes are
  defined.

## Acceptance
- A1: `/chat` renders the card layout, header, avatars, timestamps, bubbles and composer
  as described in R1–R6.
- A2: No React component file in `frontend/` exceeds 200 LOC (frontend RULE-A).
- A3: No raw one-off `<div>` structure is introduced in `shared/features/` or `app/`;
  new presentational pieces are added to `shared/ui-kit/` first (frontend RULE-B).
- A4: `pnpm test` (jest) and `pnpm lint` pass in `frontend/`.
- A5: All behavior is unchanged — send, retry, reset, attachment policy, typewriter,
  hydration and scroll pinning keep their current semantics.

## Constraints
- Tailwind v4 utilities only; no new component CSS files. Tokens live in `globals.css`.
- No new runtime dependencies. Icons are inline SVG in the ui-kit, no icon package.
- Message timestamps must come from existing message data; if the message type has no
  timestamp field, add it through the existing type/store/service layers rather than
  deriving it in a presentational component.
- English only in all files.
