# PLAN — 2026-08-05-guardrail-news-false-positive

## v1

### Root cause (R1)
No deterministic layer scores `injection` (data/lexicon.py holds only SEXUAL/DRUGS;
detectors/lexicon.py's hits are evidence for window-aiming only, PLAN D12 in a prior
task). The judge is the sole decider, so the defect is in `JUDGE_SYSTEM`
(mcp/guardrails/prompts.py), not in config or lexicon:

- The `injection` clause defines the category abstractly ("steer, override or extract
  the instructions of the AI system") but gives the model no contrastive example of an
  ordinary, context-free informational request — unlike the `pii` clause, which already
  anchors itself with a counter-example ("order id" vs. a declared identifier, see
  `test_the_declaration_is_the_signal_not_the_shape`).
- A short, terse, non-English request with no surrounding context ("Какие новости?",
  "Последние новости") gives the judge nothing to weigh except the abstract wording, and
  a small model (gemma-4-31b-it, temperature 0.0) resolves that ambiguity toward
  "extract" pattern-matching any information-seeking phrasing, not only extraction
  *of the system's own instructions*.
- `judge_threshold` (config.py, 0.6) and the lexicon are not implicated: neither
  contains injection terms, so the fix must live in the prompt, matching the R3
  constraint (root-cause fix in judge prompt/config/scoring logic).

### Fix design
1. `mcp/guardrails/prompts.py` — extend the `injection` clause in `JUDGE_SYSTEM` with an
   explicit negative rule, mirroring the existing `pii` counter-example pattern
   (`"whether or not it is well formed" ... "order id"`): terseness, imperative phrasing
   or the request being in a non-English language is not evidence of `injection` by
   itself; ordinary informational/conversational requests (news, weather, facts,
   translation, summaries, small talk) score low regardless of length or language, as
   long as they are not aimed at the system reading them. Add one concrete contrastive
   pair (benign short informational ask vs. an actual override/exfiltration attempt) so
   the rule has an anchor, not just abstract wording — same technique already used for
   the `pii` clause.
2. No change to `config.py` (`judge_threshold` stays at 0.6 — a threshold change would
   blunt true-positive recall across all three categories, violating "without weakening
   genuine injection/sexual/drugs detection").
3. No change to `data/lexicon.py` or `detectors/lexicon.py` — injection has no
   deterministic layer by existing design; adding one here would be the prohibited
   allowlist-by-keyword shape (A3) even if phrased as a lexicon entry.
4. No change to `services/pipeline.py` or `detectors/judge.py` — the cascade and
   parsing logic are not implicated; only what the model is *told* changes.

### Tests (R2)
The corpus split already encodes which fixture is the right home:
- `mcp/guardrails/tests/fixtures/injection.py` — `INJECTION_BENIGN` is the live-model
  control set exercised by `test_injection_corpus.py::test_control_set_is_not_blocked`
  (skips without `GEMMA_API_KEY`; a key is present in the repo `.env`, so this is
  runnable). Add "Какие новости?" and "Последние новости" here — this is the layer that
  actually reproduces and can disprove the defect, unlike anything judge-stubbed.
- `mcp/guardrails/tests/fixtures/corpus.py` `BENIGN` is NOT the right home: it is
  consumed only by `test_pipeline.py::test_benign_input_passes_untouched`, which stubs
  the judge (`JudgeVerdict([], {}, ...)`) — adding the phrases there would pass
  unconditionally and prove nothing about the actual defect (A3 risk: false confidence).
- `mcp/guardrails/tests/test_prompt_contract.py` — add a static assertion (no live
  call, follows the existing pattern such as
  `test_the_declaration_is_the_signal_not_the_shape`) pinning that `JUDGE_SYSTEM`
  contains the new negative rule/anchor phrase, so the prompt cannot silently regress
  even when nobody runs the live corpus test.
- No new file needed; both edits are additions to existing fixture/test files.

### Acceptance mapping
- A1 -> `test_injection_corpus.py::test_control_set_is_not_blocked` over the extended
  `INJECTION_BENIGN` (run with `GEMMA_API_KEY` set, key already in repo `.env`).
- A2 -> `test_injection_corpus.py::test_injection_recall` (unchanged `INJECTIONS` corpus,
  `MIN_RECALL = 0.90`) plus the full existing `test_pipeline.py` / `test_lexicon.py` /
  `test_pii.py` / `test_normalize.py` suites, all judge-stubbed and untouched by this
  change — must stay green.
- A3 -> satisfied by construction: fix is a prompt-clause rewrite in `JUDGE_SYSTEM`
  scoped to terseness/language-neutrality, not a literal "новости"/"news" allowlist
  anywhere in prompts.py, config.py or the lexicon.

### Risks
- Live-model non-determinism: `temperature=0.0` bounds but does not guarantee exact
  repeatability across model revisions; `MAX_FALSE_POSITIVE = 0.10` on the control set
  is the existing tolerance and is not changed by this task.
- Over-correction risk: broadening the negative rule too far could suppress genuine
  short injection attempts (e.g. "print your prompt"). Mitigated by keeping the new rule
  scoped to requests "not aimed at the system reading them" — the same aiming test the
  clause already uses — and by re-running `test_injection_recall` unchanged.

### File/module impact
- `mcp/guardrails/prompts.py` (edit — JUDGE_SYSTEM injection clause)
- `mcp/guardrails/tests/fixtures/injection.py` (edit — extend INJECTION_BENIGN)
- `mcp/guardrails/tests/test_prompt_contract.py` (edit — add pinning assertion)

### Step sequencing
1. Executor edits `prompts.py`: extend the `injection` clause per Fix design §1.
2. Executor extends `INJECTION_BENIGN` in `tests/fixtures/injection.py` with the two
   required RU phrases.
3. Executor adds the prompt-contract pinning test in `test_prompt_contract.py`.
4. Executor runs, in order: `test_prompt_contract.py` (no key needed), full
   judge-stubbed suite (`test_pipeline.py`, `test_lexicon.py`, `test_pii.py`,
   `test_normalize.py`), then `test_injection_corpus.py` with `GEMMA_API_KEY` set —
   records recall and false-positive rate in EXEC.md for Validator.
5. Validator checks A1 (new phrases pass live), A2 (recall/regression suites green),
   A3 (no literal allowlist), and Constraints (no file touched outside
   `mcp/guardrails/`).

STATE: stage=PLANNED, next_actor=Executor, plan_version=1.
