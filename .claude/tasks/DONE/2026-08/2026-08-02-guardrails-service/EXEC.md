# EXEC — 2026-08-02-guardrails-service

## v1

### Delivered

**`guardrails/`** — new distribution, own container, Python 3.12 pin.
`config.py` (all thresholds/timeouts/toggles env-backed, R10) · `schemas/verdict.py`
(three-valued `Decision`, `PII_NOTICE_TEMPLATE` defined once, R2/R5/R13) ·
`detectors/{normalize,lexicon,pii,judge}.py` · `data/lexicon.py` · `prompts.py` ·
`services/{pipeline,review_store}.py` · `routers/check.py` · `main.py` · `README.md` ·
`.env.example` · `Dockerfile` · 182 tests.

**Call sites.** `mcp/agent_core/guardrails.py` — shared client with mirrored contracts
and the fail policy (R8). Gates in `master_orchestrator/services/orchestrator.py`
(R6a/R6c, ordered per D5a) and `doc_analyzer/services/analyze_service.py` (R6b).
`GuardrailInfo` on `OrchestrationResult`; gateway untouched, as amended.

**Frontend.** `GuardrailInfo` in `types/chat.d.ts`, wire mapping in `chatService.ts`,
carried through `chatStore`, rendered by `MessageBubble` as a footnote. The R5 notice is
shown in english verbatim — it is the exact sentence the model was given, and a
paraphrase would be a different claim.

**Infra.** `guardrails` service in `docker-compose.yml` with a healthcheck; `mcp` now
depends on it being healthy. `mcp/.env.example` extended.

### Verification run

| Suite | Result |
|---|---|
| `guardrails/tests` (182) | pass — `GUARDRAILS_PII_USE_NLP=false` |
| `mcp/tests` (6) | pass |
| `ruff` on all new/changed python | clean |

Both suites were executed in a Linux container, not on the dev machine: `mcp/.venv`
holds a macOS interpreter path and cannot run under the mounted workspace. Not executed:
`docker compose up` (A6's build half) and the frontend jest suite.

### Defects the tests found

1. **The lexicon did not work in english at all.** Normalization folds latin glyphs onto
   their cyrillic twins, but terms were matched raw — the text was folded and the
   dictionary was not, so `heroin` became `неrоin` and matched nothing. Terms now go
   through the same normalization, and a third "collapsed" form (separators removed)
   catches `к-о-к-а-и-н` and `b u y  w e e d`.
2. **Presidio does not detect russian phone numbers.** Its built-in recognizer is
   region-list driven and RU is not in it, so `+7 916 …` passed straight through. Added a
   pattern recognizer anchored on the country code — an unanchored digit-run pattern
   swallowed SNILS and INN, which are also separated digit runs.
3. **`наркотик` misses `наркотической`** — the stem is `наркотич-`. Changed to `наркот`.
   Deliberately not `нарко`, which would match `наркоз` (anesthesia) — the opposite of
   what should be flagged.
4. **The lexicon out-voted the judge on medical context.** "Купить траву без рецепта"
   contains "рецепт", so procurement was reaching `review` instead of `blocked`. The
   judge's opinion now decides when it has one; the lexicon signal is the fallback for
   when it does not.

### Decisions taken during execution

- **`review` requires a substance, not just clinical vocabulary.** R13 as written could
  be read as holding every medical question. Holding all of them would be its own failure
  mode, so `review` fires only on drug-category ∧ medical-context. The corpus carries the
  two sets separately with different expected outcomes.
- **Controlled substances with real clinical use** (morphine, fentanyl, benzodiazepines,
  codeine, tramadol) are in the drug lexicon on purpose. The category is meant to fire on
  them; the context check is what keeps the patient from being refused.
- **`judge_on_clean` defaults false.** When the lexicon finds nothing the judge is
  skipped — cheap, and blind to phrasing the lexicon does not carry. The toggle exists and
  is documented; turning it on is a cost/latency decision with numbers attached, not a
  default.
- **An unparseable judge reply yields no category** rather than a guess. The cascade still
  has the lexicon's evidence to fall back on.
- **`review_timeout_s` defaults 0** (hold forever). Auto-resolving stale cases is the
  policy decision PLAN R-7 left to the Engineer; the knob is wired, the default declines
  to decide.

### Open items for the Validator

- A4's numbers are not recorded: latency was not measured under load. The fast path is
  sub-millisecond in unit tests, but no p95 for the full input check exists.
- A6 is half-verified — tests and ruff pass, `docker compose up` was not run.
- A1's false-positive observation on the benign control set is not quantified beyond
  "the 12 benign cases pass".
- PLAN R-4 (prompt injection inside documents) remains explicitly out of scope.
