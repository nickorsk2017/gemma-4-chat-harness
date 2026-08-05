# PLAN — 2026-08-05-pii-redaction-orchestration

## v1

### F — Findings that precede any design

- F1: R1, R2 and R6 are already implemented. `master_orchestrator/services/orchestrator.py`
  calls `check_input` before the tool loop and before `store.save`, replaces the prompt with
  `verdict.text`, and drops the original for the rest of the turn. `agent_core/guardrails.py`
  is fail-closed on the input path (`GuardrailsUnavailable`). Only redacted text is persisted.
- F2: The reported defect is therefore NOT a missing enforcement point. It is detector
  coverage. `guardrails/detectors/pii.py` matches `RU_PASSPORT` only on a 4+6 digit shape and
  `PHONE_NUMBER` only behind a `+CC` or leading-`8` anchor. The A1 sample carries an 8-digit
  and a 6-digit run: no recognizer matches, the verdict returns the text unchanged, and the
  model legitimately reads back what the thread legitimately stored.
- F3: Consequence for the task as written — A1 cannot pass by changing the orchestration
  layer, because the orchestration layer is not where the miss happens. C1 fixes the
  injection point at a layer that already does its job.

### D — Decisions

- D1: Scope is corrected to the detector layer of `guardrails`. Orchestration is read-only in
  this task. This contradicts C1/R2 as written and is raised as I-1 below rather than decided
  unilaterally.
- D2 (R3): Keep the existing typed placeholder (`<RU_PASSPORT>`, `<PHONE_NUMBER>`). A flat
  `HIDDEN` marker is a regression: the type feeds `known_pii_types` into the output gate,
  which is what detects a value coming back out, and it feeds `PII_NOTICE_TEMPLATE`. Both
  degrade to "something was hidden". R3 offers flat-vs-typed as an open choice; it is not
  open — the typed form is load-bearing.
- D3 (R4): Reverse substitution is OUT of scope, and should stay permanently out. Restoring a
  value requires storing the value, which reintroduces raw PII into exactly the persistence
  path R2 exists to keep it out of. The current design keeps no map by construction; adding
  one trades the guarantee for a convenience.
- D4 (coverage): Add a declared-PII recognizer — a keyword anchor (`паспорт`/`passport`/
  `телефон`/`phone`/`номер`) followed within a short window by a digit run of unconstrained
  length. Redact on the user's own declaration rather than on the number's shape. This is the
  only rule that catches the A1 sample, because the sample is not a well-formed passport or
  phone number and no format rule can be made to match it without matching arbitrary integers.
- D5 (scoring): The new recognizer has no checksum, so it cannot use the promotion-to-1.0 path
  in `_scan`. It carries a score at or above `pii_score_threshold` on the strength of the
  keyword alone, and the keyword window is what bounds the false-positive rate — not the digit
  count. Overlap with an existing typed span resolves in favour of the existing span, so a
  well-formed passport is still reported as `RU_PASSPORT`.
- D6 (judge): Do NOT route this through `detectors/judge.py`. Its `OTHER` class could catch a
  declared number, but the judge sees the value in order to find it — the module's own docstring
  records this as the honest caveat of the unstructured path. Structured-by-declaration data
  can be masked before any model call, and should be.

### M — Impact map

- `guardrails/detectors/pii.py` — new recognizer, its score, its placement in `RECOGNIZERS`.
- `guardrails/config.py` — the toggle and the keyword window, env-backed per the module's
  existing rule that no policy constant is hardcoded.
- `guardrails/tests/test_pii.py` — A3's three cases.
- No change in `master_orchestrator`, `agent_core`, gateway or frontend.

### S — Sequence

1. Engineer resolves I-1 and I-2 (this plan cannot proceed past approval with either open).
2. Add the recognizer and its config toggle.
3. Tests: A1 sample positive; ordinary numbers negative (an order id, a year, a price with no
   keyword nearby); keyword-without-digits negative; fail-closed on an unreachable gate.
4. Confirm the existing orchestration tests still assert gate-before-persist, unmodified.

### R — Risks

- R-1 (C2, blocking on the numbers): The 66 s budget in C2 exists nowhere in the code.
  `master_orchestrator/config.py` sets `turn_budget_s: float = 60.0`. The input gate is
  single-shot at 15 s; the output ladder is bounded at 35 s. Either C2 is wrong or the config
  is. Measured contribution of this change is ~0 — a compiled regex over one prompt, inside a
  gate call that already happens on every turn. A4 is satisfiable, but the budget it measures
  against has to be the real one first.
- R-2: False positives are now possible on a sentence like "заказ номер 4443" — a real cost
  that D4 accepts deliberately, since the alternative is not redacting what the user explicitly
  labelled as a passport. The keyword window is the only tuning surface; widening it widens
  this risk.
- R-3: The recognizer is language-coupled (Russian and English keywords). A third UI language
  silently loses coverage, with no failing test to announce it.
- R-4: `guardrails/schemas/verdict.py` carries `MEDICAL_DISCLAIMER` twice, verbatim. Unrelated
  to this task, not fixed here, flagged for a separate ticket.

### I — Issues for the Engineer (HIGH approval gate)

- I-1 (requirement): R1/R2/R6 describe work that is already done, and C1 forbids planning a
  change in the layer that actually needs one. TASK.md needs to be restated as a detector-
  coverage task before EXEC begins.
- I-2 (requirement): C2's 66 s contradicts `turn_budget_s = 60.0`. State which is normative.

## v2

Re-planned on the Engineer's amended TASK.md (international identifiers, LLM-layer coverage).
v1 above stands except where superseded here: D4/D5 are withdrawn, D6 is reversed.

### F — Findings

- F4 (root cause, supersedes F2 as the primary): the judge is instructed NOT to report exactly
  these values. `guardrails/prompts.py`, `pii` section: *"Do not list things that have a format
  — phone numbers, passports, SNILS, INN, emails, cards, IBANs are already removed before you
  see this text."* The two layers were designed as a partition — patterns take the formatted
  types, the model takes names and addresses. The partition leaks: a value that *is* a passport
  but does not match the pattern falls between them. The deterministic layer skips it for want
  of a format, and the model skips it because it was told that layer already handled it.
- F5 (confirms F4 against the screenshot): the judge was running. Had it been unreachable,
  `_no_opinion` blocks on the INPUT direction and the turn would have been refused outright.
  The turn was answered, so a verdict came back — an ALLOWED one, from a model obeying its
  prompt. Nothing malfunctioned; the prompt is the defect.
- F6: `_mask_model_pii` coerces any unrecognised type to `PERSON` (`_MODEL_PII_TYPES` is
  `PERSON|LOCATION|OTHER`). Widening the prompt alone would mask a DNI and label it a person's
  name — the notice and the output gate's `known_pii_types` would both then be wrong.

### D — Decisions (v2)

- D7 (reverses D6): open-ended identifiers are the judge's job. Per TASK R3 the alternative is
  a regex per country, which is unbounded by construction. The cost D6 objected to — the model
  sees the value — is accepted and stated plainly: the judge runs *inside* guardrails, before
  the answering model and before persistence, so the value's exposure ends at the gate. This is
  the same trade already accepted for names and addresses.
- D8: add an `ID_NUMBER` type to the judge's taxonomy and to `_MODEL_PII_TYPES` together, in one
  change. Doing either alone is F6.
- D9: rewrite the prompt's exclusion into a positive instruction: report an identifier whenever
  the surrounding text declares it as one, whether or not it looks well-formed; skip only what
  is already a `<PLACEHOLDER>`. The declaration is the signal, not the shape.
- D10 (withdraws D4/D5): no keyword-anchored regex. It was the best available answer while the
  model was ruled out; with D7 it is a second mechanism for one job, and the weaker one.
- D11: the deterministic layer is untouched (TASK R4). Well-formed RU types keep resolving there
  with their own entity names and checksum promotion — that is what A4 asserts.

### M — Impact map (v2)

- `guardrails/prompts.py` — the `pii` section of `JUDGE_SYSTEM`.
- `guardrails/detectors/judge.py` — nothing structural; `_parse` already passes types through.
- `guardrails/services/pipeline.py` — `_MODEL_PII_TYPES` gains `ID_NUMBER`.
- `guardrails/tests/` — A1–A5.
- Unchanged: `detectors/pii.py`, `master_orchestrator`, `agent_core`, gateway, frontend.

### R — Risks (v2)

- R-5: prompt-level coverage is not testable by the strongest assertion the pattern layer
  enjoys. A model can miss. A1/A2 pin the reported cases; a class of miss remains that no test
  will announce. This is inherent to R3's choice of mechanism, not to this plan.
- R-6: false positives move from "tunable window" (withdrawn D4) to model judgement. An order
  id in a sentence that also says "паспорт" is the shape of the failure.
- R-7 (A6): no new model call — the judge already runs on every input turn. The delta is prompt
  tokens only, inside the existing 8 s `judge_timeout_s`, which is itself inside the normative
  60 s turn budget. A6 is satisfiable and the risk is closed.
- R-8: R-3 from v1 survives and widens — the prompt names its languages, and identifier
  vocabulary is now global ("DNI", "NIE", "CURP", "Aadhaar"). Coverage of a term the prompt
  never names rests entirely on the model's own knowledge.

### I — Issues (v2)

- I-1: RESOLVED by the amended TASK.md.
- I-2: RESOLVED. The Engineer withdrew the 66 s figure; `turn_budget_s = 60.0` is normative and
  unchanged by this task.

No open issues. Awaiting the HIGH approval gate before EXEC.

