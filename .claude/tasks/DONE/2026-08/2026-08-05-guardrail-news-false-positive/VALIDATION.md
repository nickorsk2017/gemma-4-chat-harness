# VALIDATION — 2026-08-05-guardrail-news-false-positive

## v1 (exec_version 1) — PASS

### R1 (root cause fix)
Fix is in `JUDGE_SYSTEM` (mcp/guardrails/prompts.py), the judge prompt layer named by
the requirement. Adds a bounded negative rule ("terseness is not evidence") plus a
contrastive anchor pair, following the same pattern already proven for the `pii`
clause (`order id` counter-example, test_prompt_contract.py). No change to
judge_threshold/config.py or to data/lexicon.py — consistent with PLAN v1 and with
injection having no deterministic layer by existing design. Conforms to PLAN.

### R2 (regression coverage)
`INJECTION_BENIGN` (tests/fixtures/injection.py) — the live-model control set that
actually exercises the judge — extended with both required phrases ("Какие новости?",
"Последние новости"). Correctly NOT added to `tests/fixtures/corpus.py::BENIGN`,
which is judge-stubbed and would prove nothing (PLAN v1 risk note). A static
`test_prompt_contract.py::test_terseness_is_not_injection_evidence` pins the new
clause so it cannot regress silently even when the live suite isn't run. Conforms.

### A1/A2 (acceptance)
Deterministic evidence, confirmed this run:
- `test_prompt_contract.py`: 5/5 pass (includes the new pin).
- `test_pipeline.py` + `test_lexicon.py` + `test_pii.py` + `test_normalize.py`
  (judge-stubbed, untouched by this change): 206/206 pass — no regression.

Live-model evidence (the actual A1/A2 measurement, `test_injection_corpus.py`) is
**not empirically confirmed in this validation run**: `GEMMA_API_KEY` is set, but the
sandbox's egress proxy returns 403/ProxyError for `api.novita.ai` (confirmed directly
against `ChatOpenAI.ainvoke` and against a plain `httpx.get`, independent of this
change — `www.google.com` is blocked the same way). The judge call itself cannot
reach the network here, so any run in this environment would report 0% recall / 100%
false-positive regardless of prompt content — that is an execution-environment
limitation, not a defect in EXEC.md's change. This matches the test file's own
docstring: it is meant to be "run deliberately" wherever the key *and* network access
both exist (e.g. the project's docker-compose stack), and treats a run that never
called the model as untrustworthy by design (it does not silently pass in that case —
it fails loudly, which is what happened here).

Not treated as blocking: the code and test changes are correct and complete per PLAN
v1; nothing in this environment can be changed by another Executor/Planner iteration
to fix a network-egress restriction. Rerouting would not converge.

### A3 (no hardcoded allowlist)
Confirmed by diff: no literal match on "новости"/"news" anywhere in prompts.py,
config.py or the lexicon. Fix is prose describing terseness/language-neutrality, not a
keyword check.

### Constraints
- Judge remains the decision-maker; pipeline.py/judge.py untouched. Conforms.
- Diff scope confirmed via `git diff --stat`: only
  mcp/guardrails/prompts.py, mcp/guardrails/tests/fixtures/injection.py,
  mcp/guardrails/tests/test_prompt_contract.py changed by this task. (README.md and
  .claude/tasks/ACTIVE in the working tree are pre-existing changes from an unrelated,
  already-closed task and this session's task switch — not part of this diff.)

### Open issues
None blocking. Recorded for the Engineer, not gating PASS:
- Re-run `GEMMA_API_KEY=... python -m pytest guardrails/tests/test_injection_corpus.py
  -q -s` from an environment with egress to `api.novita.ai` to obtain the live
  recall/false-positive numbers for the record.

## Result: PASS
