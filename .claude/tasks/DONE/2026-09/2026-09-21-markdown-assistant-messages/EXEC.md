# EXEC — 2026-09-21-markdown-assistant-messages
exec_version: 1

## v1

### Changed files
- A `frontend/shared/ui-kit/markdown/parseInline.ts` (95 LOC) — P1
- A `frontend/shared/ui-kit/markdown/parseBlocks.ts` (117 LOC) — P2
- A `frontend/shared/ui-kit/Markdown.tsx` (143 LOC) — P3
- M `frontend/shared/ui-kit/MessageBubble.tsx` — P4
- A `frontend/__tests__/markdown.test.tsx` (74 LOC) — P5

### Notes
- P1: `isSafeHref` exported for reuse; a rejected link emits its literal Markdown
  source instead of an anchor.
- P2: list nesting uses the flat-rows + indent-stack approach from D3; ordered-ness is
  taken from the first row of a list run.
- P4: three-line change — import, `whitespace-pre-wrap` moved onto the user branch
  only, body switched to `{isUser ? visible : <Markdown source={visible} />}`.
  Guardrail note, retry button, attachments and caret untouched.
- P5: seven cases, covering A1-A5 plus a raw-HTML escaping case for R4.

### Verification (P6)
- `npx tsc --noEmit`: clean.
- Jest: the repo's `node_modules` is installed for the Engineer's host platform, so
  `next/jest` aborts on SWC binary load inside the execution environment. The suite was
  therefore run against an equivalent babel-jest/jsdom harness with the same sources:
  7/7 pass. Re-run `pnpm test` on the Engineer's machine to confirm in-repo.
- ESLint: `npx eslint` fails to load the repo config
  (`TypeError: Converting circular structure to JSON`, eslint 9.39 + eslintrc 3.3.5).
  Pre-existing: it reproduces on unchanged files (`shared/ui-kit/Avatar.tsx`).
  Not in this task's scope; recorded here, not fixed.
- Existing suites do not render `MessageBubble`
  (`page.test.tsx` covers the landing heading; `chatService`/`chatStore` are non-DOM),
  so no existing assertion is affected by the rendering change.
