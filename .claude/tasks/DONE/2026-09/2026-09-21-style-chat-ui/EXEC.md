# EXEC — 2026-09-21-style-chat-ui

## v1

### Summary
- P1 — `globals.css` rewritten as the single token source: `:root` custom properties
  (page, surface, foreground, muted, hairline, accent, accent-soft, bubble surfaces,
  warning, danger, radii, card shadow), a dark redefinition of the same names, and an
  `@theme inline` bridge so Tailwind exposes them as `bg-*`, `text-*`, `border-*`,
  `rounded-*`, `shadow-card`. `body` paints the page background.
- P2 — `icons.tsx` added: star, person, refresh, paperclip, paper-plane as inline SVG
  over `currentColor`, each `aria-hidden`. `Avatar` (accent-tinted circle for the agent,
  neutral circle for the user) and `Badge` added.
- P3 — `ChatShell` added: centered max-w-3xl card on the page background with card
  radius, hairline border and soft shadow; header / scrolling transcript / composer
  slots. `ChatHeader` added (agent mark, title, badge, subtitle, action slot).
- P4 — `MessageRow` added: avatar on the speaker's side, side-aligned column, timestamp
  as a `<time>` element beneath the bubble. `formatTime.ts` implements D4's arithmetic
  `HH:MM`. `MessageBubble` reduced to the bubble body, retokenized, tail notch dropped,
  user bubble now accent + semibold.
- P5 — `HeaderButton` restyled to a hairline pill and given an `icon` slot (used for the
  refresh glyph). `MessageInput` composer wrapped in a rounded bar: circular outlined
  attach button with the paperclip glyph, pill textarea, square accent send button with
  the plane glyph; the `Send`/`📎` text labels are gone and the controls now carry
  `aria-label`s as their only accessible names ("Send message", "Attach image or PDF
  (one file)").
- P6 — empty state, typing indicator (now an assistant `MessageRow` with no timestamp),
  error banner and the attachment warning retokenized.
- P7 — `tsc --noEmit` clean. Jest and ESLint could not be executed in this environment:
  `frontend/node_modules` holds macOS-arm64 binaries (Next SWC fails to load under the
  linux sandbox, ESLint's flat-config bridge throws before linting). No test file
  asserts on the removed button text, so no test change was required; the suites must be
  re-run on the developer machine.
- Behavior untouched (A5): send/retry/reset handlers, mandatory-prompt rule,
  single-attachment policy, Enter-to-send, typewriter, hydration snapshot and scroll
  pinning were carried over unchanged.

### Changed files
- `frontend/app/globals.css` (rewritten)
- `frontend/shared/ui-kit/icons.tsx` (new)
- `frontend/shared/ui-kit/Avatar.tsx` (new)
- `frontend/shared/ui-kit/Badge.tsx` (new)
- `frontend/shared/ui-kit/ChatShell.tsx` (new)
- `frontend/shared/ui-kit/ChatHeader.tsx` (new)
- `frontend/shared/ui-kit/MessageRow.tsx` (new)
- `frontend/shared/ui-kit/formatTime.ts` (new)
- `frontend/shared/ui-kit/MessageBubble.tsx` (modified)
- `frontend/shared/ui-kit/MessageInput.tsx` (modified)
- `frontend/shared/ui-kit/HeaderButton.tsx` (modified)
- `frontend/shared/features/chat/ChatView.tsx` (modified)

### Notes
- `app/layout.tsx` and `app/chat/page.tsx` needed no change: `ChatShell` owns the page
  surface, so the route stayed a one-line server component.
