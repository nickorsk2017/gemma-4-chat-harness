# TASK — 2026-08-05-2026-08-05-russian-text-cleanup
owner: Engineer
immutable: true

## Requirements
- R1: Find every occurrence of Russian-language text (Cyrillic characters) persisted in
  repository files (source code, comments, docstrings, log/exception messages, test
  names, docs, config) and replace it with an English equivalent, per the root
  CLAUDE.md "Language — English only in files" rule.
- R2: Preserve behavior. Do not change logic, only translate embedded Russian strings
  and comments to English.
- R3: Files known so far with Cyrillic content (grep for `[а-яА-ЯёЁ]`, excluding
  `.git`, `node_modules`, `.venv*`, `__pycache__`, build output):
  - frontend/stores/chatStore.ts
  - frontend/shared/ui-kit/MessageBubble.tsx
  - mcp/guardrails/tests/test_pii.py
  - mcp/guardrails/tests/fixtures/injection.py
  - mcp/guardrails/tests/fixtures/corpus.py
  - mcp/guardrails/tests/test_normalize.py
  - mcp/guardrails/tests/test_pipeline.py
  - mcp/guardrails/prompts.py
  - mcp/guardrails/detectors/normalize.py
  - mcp/guardrails/detectors/lexicon.py
  - mcp/guardrails/detectors/pii.py
  - mcp/guardrails/data/lexicon.py
  - mcp/tests/test_gate_outage.py
  - mcp/tests/test_doc_analyzer_gate.py
  - mcp/tests/test_guardrail_gates.py
- R4: Some of the mcp/guardrails files above hold Russian text as intentional
  multilingual test/lexicon *data* (e.g. Russian PII/injection detection samples),
  not stray comments. Planner must decide, per file, whether the Cyrillic content is:
  (a) an English-only violation to translate in place, or
  (b) functional multilingual test data that must remain Cyrillic to test Russian-
      language detection, in which case it is out of scope and Planner records why.

## Acceptance
- A1: Every non-functional Russian string (comments, docstrings, log/exception
  messages, identifiers, doc prose) across the repo is translated to English.
- A2: Any Cyrillic content deliberately left in place (multilingual test fixtures) is
  explicitly justified in PLAN.md/EXEC.md and does not trip the English-only rule
  unjustified.
- A3: `grep -rlP '[а-яА-ЯёЁ]'` over source directories (excluding build/dep dirs)
  returns only the justified exceptions from A2, if any.
- A4: Existing tests still pass after translation.

## Constraints
- Do not touch files outside the list in R3 unless the Planner's search finds
  additional Cyrillic content not yet enumerated (then add it to PLAN.md).
- No logic changes beyond string/comment translation.
