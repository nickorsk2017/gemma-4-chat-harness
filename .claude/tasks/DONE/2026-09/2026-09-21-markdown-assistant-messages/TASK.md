# TASK — 2026-09-21-markdown-assistant-messages
owner: Engineer
immutable: true

## Requirements
- R1: Assistant message content MUST be rendered as formatted Markdown in the chat UI
  instead of raw text. Today an answer containing `*` bullets and `**bold**` is shown
  verbatim with its markup characters.
- R2: Supported syntax: headings, bold, italic, inline code, fenced code blocks,
  ordered and unordered lists including nested levels, links, blockquotes,
  horizontal rules, and paragraph breaks. Unsupported or malformed syntax MUST
  degrade to plain text, never throw.
- R3: No new runtime dependency. The renderer is implemented in-repo.
- R4: Rendering MUST NOT inject raw HTML from message content into the DOM
  (no `dangerouslySetInnerHTML`); Markdown is parsed into React elements and any
  HTML-looking text in the content is rendered as text.
- R5: User messages keep their current plain-text rendering.
- R6: The existing typewriter reveal MUST keep working: a partially revealed prefix
  renders without visual breakage, and the guardrail note, retry action, attachments
  and caret keep their current behaviour and position.
- R7: The renderer is a `shared/ui-kit/` presentational primitive consumed by
  `MessageBubble` (frontend CLAUDE.md RULE-B); every file stays within the 200-LOC
  component cap (RULE-A).
- R8: Link targets rendered from message content MUST open safely
  (`target="_blank"`, `rel="noopener noreferrer"`) and non-http(s) schemes
  (e.g. `javascript:`) MUST NOT become active links.

## Acceptance
- A1: A frontend test asserts that an assistant message with `**bold**`, a `*` list
  and a heading renders as `<strong>`, `<ul>/<li>` and a heading element, with no
  literal `*` or `#` characters left in the output.
- A2: A frontend test asserts a fenced code block renders as `<pre><code>` with its
  content unescaped and unformatted (no bold applied inside code).
- A3: A frontend test asserts a user message with Markdown characters is still
  rendered verbatim as text.
- A4: A frontend test asserts a truncated prefix (mid-syntax, e.g. `**bo`) renders
  without throwing.
- A5: A frontend test asserts a `javascript:` link is not rendered as an anchor and
  that an `http(s)` link is rendered with `rel="noopener noreferrer"`.
- A6: Existing frontend tests still pass; `pnpm lint` and `tsc` are clean.

## Constraints
- No new runtime or dev dependency in `frontend/package.json`.
- Styling via Tailwind v4 utility classes only.
- English only in all files (root CLAUDE.md).
