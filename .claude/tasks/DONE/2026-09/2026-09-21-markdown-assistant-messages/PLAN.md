# PLAN — 2026-09-21-markdown-assistant-messages
plan_version: 1

## v1

### D1 — In-repo renderer, no dependency (R1, R3)
A hand-written parser is chosen over a library because R3 forbids new dependencies.
Scope is bounded by R2, so a line-oriented block parser plus a single-pass inline
parser is sufficient; anything outside that grammar falls through to a text paragraph,
which satisfies the degrade-to-text half of R2.

### D2 — Layer placement (R7)
Three new files under `shared/ui-kit/`:
- `markdown/parseBlocks.ts` — pure text -> block AST (no React).
- `markdown/parseInline.ts` — pure block text -> inline AST (no React).
- `Markdown.tsx` — presentational component mapping the AST to React elements.
Parsers live outside the component file so `Markdown.tsx` stays a thin renderer and
each file remains well under the 200-LOC cap (RULE-A). `MessageBubble` consumes
`<Markdown>` as a kit primitive (RULE-B); no feature or page file changes.

### D3 — Block grammar (R2)
Recognised at line level, in this precedence order: fenced code (``` open/close),
ATX heading (1-6 `#` + space), horizontal rule (`---`/`***`/`___` alone on a line),
blockquote (`>` prefix, recursively parsed as blocks), list item
(`-`/`*`/`+`/`N.` + space, nesting by leading-space count in units of two),
blank-line-separated paragraph. Fenced code is claimed first so its body is never
re-interpreted as blocks (A2). An unterminated fence is treated as code to the end of
input, which is the correct behaviour for a streaming prefix (R6/A4).

### D4 — Inline grammar (R2, A2)
Applied to heading, paragraph, list-item and blockquote text only, never to code
block bodies. Order: inline code (backtick pair) claimed before emphasis, so markup
inside code stays literal; then link `[text](url)`; then `**bold**`/`__bold__`; then
`*italic*`/`_italic_`. An unmatched opening delimiter emits its literal characters,
which is what makes a truncated prefix safe (A4) rather than a parse error.

### D5 — Safety (R4, R8)
Output is React elements only; no `dangerouslySetInnerHTML` anywhere, so text that
looks like HTML is escaped by React itself (R4). Link URLs are checked against an
allow-list of schemes (`http:`, `https:`, `mailto:`) plus relative paths; a rejected
URL emits the original Markdown source as text rather than an anchor (A5). Accepted
anchors get `target="_blank" rel="noopener noreferrer"`.

### D6 — Bubble integration (R5, R6)
`MessageBubble` currently renders `{visible}` inside a `whitespace-pre-wrap`
container. Change: user role keeps the raw `{visible}` text node and the
`whitespace-pre-wrap` class; assistant role renders `<Markdown source={visible} />`
and drops `whitespace-pre-wrap` on that branch (the renderer produces real block
elements; keeping it would double the vertical rhythm). The typewriter, guardrail
note, retry button, attachments and caret are untouched — `Markdown` receives the
same `visible` string the text node received, so re-parsing per tick is the only
behavioural change, and it is bounded by reply length.

### D7 — Styling (R2, constraints)
Tailwind v4 utilities applied per element inside `Markdown.tsx` (no `prose` plugin —
not a dependency in this repo). First block gets no top margin so a one-paragraph
answer keeps the current bubble padding. Code uses the existing `bg-surface` /
`text-muted` tokens already present in the kit, so light/dark theming comes for free.

### D8 — Tests (A1-A6)
`__tests__/markdown.test.tsx` covers A1, A2, A4, A5 against `Markdown` directly and
A3 against `MessageBubble` with `role="user"`. Existing suites unchanged (A6).

### Risks
- RK1: Re-parsing on every typewriter tick. Bounded by reply size; if a profile ever
  shows it, memoisation on `source` is the fix — not planned now (no evidence).
- RK2: Grammar gaps (tables, images, task lists) are out of R2 scope by design and
  degrade to text; adding them later is a new task, not an Executor improvisation.

### Sequencing
P1 `markdown/parseInline.ts` -> P2 `markdown/parseBlocks.ts` -> P3 `Markdown.tsx`
-> P4 `MessageBubble.tsx` integration -> P5 tests -> P6 lint + tsc + jest.
