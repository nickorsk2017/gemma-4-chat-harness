# PLAN — 2026-08-05-2026-08-05-russian-text-cleanup

## v1

### Classification (R4)
Grep of `[а-яА-ЯёЁ]` across source dirs (excl. `.git`, `node_modules`, `.venv*`,
`__pycache__`, build output) resolves to two groups:

**Group A — English-only violations (translate):**
- `frontend/stores/chatStore.ts:7` — `TURN_TIMEOUT_MESSAGE` constant, user-facing
  string `"Повторите запрос"`. Used at line 141 as placeholder assistant message.
- `frontend/shared/ui-kit/MessageBubble.tsx:98` — button/label text `"Повторить"`.

These are stray untranslated UI copy, not tied to any Russian-language detection
logic. In scope per R1/A1.

**Group B — functional multilingual data (out of scope per R4b):**
- `mcp/guardrails/**` (prompts.py, detectors/{normalize,lexicon,pii}.py,
  data/lexicon.py, tests/**) and `mcp/tests/{test_gate_outage,
  test_doc_analyzer_gate,test_guardrail_gates}.py`.
- This module is a Russian-language PII/content-moderation guardrail: lexicon
  entries, transliteration/homoglyph maps, regex patterns, and test fixtures are
  Russian words/phrases the detector must match (e.g. `"наркотик"`,
  `"мой паспорт 44432423"`, `"телефон +7 916 123-45-67"`). Translating these to
  English would silently disable Russian-language detection and break the tests'
  stated intent (`plain-ru`, homoglyph/padding evasion cases). Left as-is; this
  satisfies A2 (justified exception) and is excluded from A3's grep-clean scope.

### Steps
1. Executor edits `frontend/stores/chatStore.ts:7` — replace
   `"Повторите запрос"` with an English equivalent (e.g. `"Please repeat your
   request"`), matching how the string is used as a timeout placeholder message
   (see call site at line 141).
2. Executor edits `frontend/shared/ui-kit/MessageBubble.tsx:98` — replace
   `"Повторить"` with an English equivalent (e.g. `"Retry"`), matching the
   surrounding button semantics (retry/re-send action).
3. Executor re-runs the Group A grep to confirm no other Cyrillic remains in
   `frontend/**` (excl. build/deps).
4. Executor runs the frontend test/build check available in the repo (per
   `frontend/CLAUDE.md`) to confirm no regressions from the string changes.
5. Executor does NOT touch any `mcp/guardrails/**` or `mcp/tests/test_gate_outage.py`
   / `test_doc_analyzer_gate.py` / `test_guardrail_gates.py` file — Group B is out
   of scope, per this plan's classification.

### Risk
- Low: two literal string replacements, no logic change. Risk is limited to
  translation wording matching the existing English tone used elsewhere in the
  same components (Executor should check sibling strings for tone/casing
  convention before finalizing wording).
