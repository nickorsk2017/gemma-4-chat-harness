# PLAN — 2026-09-21-style-chat-ui

## v1

### Decisions
- D1 (R7): Design tokens are CSS custom properties declared on `:root` in
  `app/globals.css` and exposed to Tailwind v4 through an `@theme inline` block, so the
  components keep using utility classes and never hard-code hex values. Token groups:
  page background, card surface, bubble surfaces, accent, accent-foreground, muted text,
  hairline border, avatar tint, radius scale, card shadow. Dark scheme redefines the
  same names under `prefers-color-scheme: dark`; no component branches on scheme.
- D2 (R1): The page shell (centered card on a padded neutral page) is a new ui-kit
  primitive rather than markup in `ChatView` or the route, satisfying RULE-B. The route
  stays a one-line server component.
- D3 (R3): Avatars, timestamps and bubble alignment belong to one presentational row
  primitive that wraps `MessageBubble`; `MessageBubble` keeps sole responsibility for
  the bubble body (content, attachments, guardrail note, retry, caret). This keeps both
  files well under the RULE-A cap and keeps the typewriter logic untouched.
- D4 (R3, constraint 3): The timestamp source already exists — `ChatMessage.createdAt`
  (epoch millis). No type, store or service change is required; the presentational layer
  only formats it. Formatting must be deterministic and locale-independent (fixed
  2-digit 24h `HH:MM`, derived arithmetically from the epoch value) so a restored
  transcript cannot produce a hydration mismatch or machine-dependent output.
- D5 (R2, R5): Glyphs (star, person, refresh, paperclip, paper plane) are inline SVG
  ui-kit primitives with no external package, one small icon module, `currentColor`
  fills, `aria-hidden` (the accessible name stays on the surrounding control).
- D6 (R5): The composer's send and attach controls lose their text labels, so their
  existing `aria-label`s become the only accessible names and must be preserved. The
  mandatory-prompt rule, single-attachment policy and Enter-to-send behavior are
  untouched (A5) — this step is presentational only.
- D7 (R2): The header "Chat" pill is a ui-kit badge primitive; the reset control keeps
  the existing `HeaderButton` component, restyled to the pill shape with an optional
  leading icon slot rather than a second button component.

### Impact map
- `app/globals.css` — token declarations, theme bridge, page background (D1).
- `app/layout.tsx` — body-level page background/centering only if D2 does not cover it.
- `shared/ui-kit/` — new: page/card shell, message row (avatar + timestamp), avatar,
  badge, icon set; modified: `MessageBubble`, `MessageInput`, `HeaderButton`.
- `shared/features/chat/ChatView.tsx` — composition only: swap raw wrappers for the new
  primitives, pass `createdAt` down, restyle empty/typing/error states (R6).
- `__tests__/page.test.tsx` — expectations that assert on removed button text ("Send")
  or on wrapper structure must be updated to query by accessible name instead.

### Steps
1. Tokens and page surface (D1) — `globals.css` first, so every later step consumes
   names rather than literals.
2. Icon module + avatar + badge primitives (D5, D7).
3. Shell/card primitive (D2); `ChatView` adopts it with no behavior change.
4. Message row primitive with avatar, alignment and timestamp (D3, D4); `MessageBubble`
   reduced to the bubble body and restyled (R4).
5. Header restyle (R2) and composer restyle (R5, D6).
6. Empty / typing / error / attachment-warning states (R6).
7. Test and lint pass; update the assertions identified in the impact map (A4).

### Risks
- RK1: Locale/timezone-dependent time formatting breaks determinism — mitigated by D4.
- RK2: Dropping the "Send" text breaks existing tests and screen-reader naming —
  mitigated by D6 and step 7.
- RK3: Absorbing avatar and timestamp into `MessageBubble` instead of a separate row
  would push it toward the RULE-A cap and entangle it with the typewriter effect —
  mitigated by D3.
- RK4: Hard-coded colors leaking into components would defeat R7 — the Validator checks
  for literal hex/`bg-gray-*`/`bg-blue-*` values outside `globals.css`.
