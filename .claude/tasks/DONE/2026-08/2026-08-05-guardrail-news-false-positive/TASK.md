# TASK — 2026-08-05-guardrail-news-false-positive
owner: Engineer
immutable: true

## Requirements
- R1: The guardrails input pipeline (mcp/guardrails/) currently blocks benign,
  neutral Russian news queries (reproduced with "Какие новости?" and
  "Последние новости") with a stable BLOCKED verdict, surfaced to the user as
  REFUSAL_INPUT via the orchestrator. Root cause: neither the lexicon
  (mcp/guardrails/data/lexicon.py) nor PII masking match these strings; the
  Gemma judge (mcp/guardrails/detectors/judge.py, prompt in
  mcp/guardrails/prompts.py) runs at temperature=0.0 and reproducibly scores
  one or more categories (most likely `injection`) above judge_threshold=0.6
  (mcp/guardrails/config.py) for these short, terse Russian phrases. Fix the
  false positive so ordinary informational/news queries in Russian (and
  equivalent English phrasing) are not blocked, without weakening genuine
  injection/sexual/drugs detection.
- R2: Add regression coverage (fixtures/tests) for benign Russian short
  queries, including at minimum "Какие новости?" and "Последние новости", so
  this class of false positive cannot silently regress.

## Acceptance
- A1: Sending "Какие новости?" and "Последние новости" through the guardrails
  input pipeline yields an allowed verdict (not BLOCKED), verified by an
  automated test.
- A2: Existing injection/sexual/drugs detection test fixtures
  (mcp/guardrails/tests/fixtures/injection.py and any sibling fixture files)
  continue to pass — no regression in true-positive blocking.
- A3: Root-cause fix lives in the judge prompt/config/scoring logic (or
  equivalent deterministic layer) in mcp/guardrails/, not a hardcoded
  allowlist keyed on the literal word "новости"/"news".

## Constraints
- Must not disable or bypass the guardrails pipeline; the judge remains the
  decision-maker per existing design (mcp/guardrails/services/pipeline.py).
- No changes outside mcp/guardrails/ (and its tests) unless the Planner
  determines the orchestrator call site also needs adjustment.
