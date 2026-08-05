# EXEC — 2026-08-05-pii-redaction-orchestration

## v1

Implements PLAN v2 (D7–D11). No change outside `mcp/guardrails`.

### Changes

- `guardrails/prompts.py` — `JUDGE_SYSTEM`, `pii` section rewritten (R1, R3, R5).
  The exclusion ("Do not list things that have a format ... already removed before you see
  this text") is gone; it was the defect. Replaced by a positive instruction: report an
  identifier of any country whenever the text presents it as one, well formed or not, with
  the counter-example ("order id, a year, a price, a version") bounding it. Type vocabulary
  is now stated in the prose, not only in the JSON schema line, which also gained
  `ID_NUMBER`.
- `guardrails/services/pipeline.py` — `_MODEL_PII_TYPES` gains `ID_NUMBER` (D8), with the
  comment recording why it is the same change as the prompt: the fallback rewrites an
  unknown type to `PERSON`, so the prompt alone would mask a DNI and label it a name.
- `guardrails/tests/test_pipeline.py` — five cases appended: A1 (both reported values),
  A2 (DNI typed as itself), A3 (ordinary numbers untouched), A4 (well-formed RU type still
  deterministic), A5 (judge down -> input refused).
- `guardrails/tests/test_prompt_contract.py` — new. Asserts the instruction itself: the
  offered types match `_MODEL_PII_TYPES`, and the removed sentence stays removed. Every
  other test stubs the judge, so nothing else covers the prompt — which is exactly where
  the defect lived and where it would silently return.

### Not changed

- `guardrails/detectors/pii.py` (R4), `master_orchestrator`, `agent_core`, gateway,
  frontend. Enforcement point and ordering were already correct (PLAN F1).

### Verification

`python3 -m pytest guardrails/tests -q` -> 210 passed, 2 skipped.

### Notes for the Validator

- A2's coverage of an arbitrary country rests on the model, not on an assertion. The tests
  stub the judge, so what is proven here is that an `ID_NUMBER` finding is handled
  correctly end to end, plus that the prompt asks for one. Whether a given model complies
  is not testable in this suite (PLAN R-5).
- PLAN R-4 (duplicated `MEDICAL_DISCLAIMER` in `schemas/verdict.py`) is untouched, as
  planned — out of scope, wants its own task.
