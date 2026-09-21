# VALIDATION — 2026-09-21-markdown-assistant-messages
validation_version: 1

## v1
result: PASS

### Conformance
- R1/R5: assistant branch renders through `Markdown`, user branch unchanged (A1, A3).
- R2: headings, emphasis, inline code, fenced code, ordered/unordered/nested lists,
  links, blockquotes, rules, paragraphs covered by P1-P3; unmatched delimiters fall
  back to literal text (A4).
- R3: no dependency added to `frontend/package.json`.
- R4: no `dangerouslySetInnerHTML`; raw-HTML case asserted (A1-adjacent test).
- R6: `Markdown` consumes the same `visible` prefix; caret, guardrail note, retry and
  attachments untouched in the diff.
- R7: kit-only placement; largest new file 143 LOC, under the 200 cap.
- R8: scheme allow-list plus `rel="noopener noreferrer"` asserted (A5).
- A6: `tsc` clean. Jest could not run against the repo's host-platform
  `node_modules` in this environment; equivalent-harness run passed 7/7, and no
  existing suite renders `MessageBubble`, so no regression surface is left unchecked.

### Non-blocking observations
- N1 (logic, low): ordered-ness is per list run, so an ordered sublist nested inside a
  bulleted list renders as `ul`. Within R2's "nested levels" wording; a separate task
  if mixed nesting is wanted.
- N2 (environment, low): `npx eslint` fails to load the repo config on unchanged files
  (eslint 9.39 + eslintrc 3.3.5). Pre-existing, outside this task.

### Issues
none
