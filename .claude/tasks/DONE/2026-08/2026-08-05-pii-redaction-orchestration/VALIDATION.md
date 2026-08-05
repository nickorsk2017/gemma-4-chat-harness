# VALIDATION — 2026-08-05-pii-redaction-orchestration

## v1

result: PASS
validation_version: 1
issues: []

### Acceptance

| id | verdict | evidence |
|----|---------|----------|
| A1 | PASS | `test_an_undetectable_passport_number_is_masked_by_the_model` — both values gone, two `<ID_NUMBER>`, one redaction entry of count 2. |
| A2 | PASS (bounded, see L-1) | `test_a_foreign_identifier_is_masked_as_itself_not_as_a_person` + `test_prompt_contract.py`. |
| A3 | PASS | `test_an_ordinary_number_is_left_alone` — order id, year, version untouched, no notice. |
| A4 | PASS | `test_a_well_formed_ru_type_still_resolves_deterministically` — `PHONE_NUMBER`, not `ID_NUMBER`. `detectors/pii.py` unchanged (R4). |
| A5 | PASS | `test_an_identifier_turn_is_refused_when_the_judge_is_down` — INPUT blocks on no opinion. |
| A6 | PASS | No call site added. `pipeline.check` calls `judge_layer.judge` exactly once per check, as before; the delta is prompt tokens inside `judge_timeout_s = 8.0`, itself inside `turn_budget_s = 60.0` (C2). |

### Requirements

R1/R3/R5 met by the prompt rewrite; R2 held by not touching the orchestrator; R4 held by not
touching `detectors/pii.py`; R6 held — typed placeholders retained and `ID_NUMBER` added to
`_MODEL_PII_TYPES` in the same change, which is what keeps the type honest downstream; R7
correctly absent; R8 unchanged and covered by A5; R9 — no new logging.

### Checks run

- `pytest guardrails/tests -q` -> 210 passed, 2 skipped.
- `ruff check guardrails/` -> 3 findings, ALL pre-existing and in files this task did not
  touch or did not touch at the reported line: `PLE2502`/`PLE2515` in `detectors/normalize.py`
  (deliberate zero-width class), `I001` on the `pipeline.py` import block, which predates this
  change (the diff is 7 lines, none of them imports). Not introduced here; not fixed here.
- `pytest mcp/tests` could not be collected in this environment (`langchain_core` absent).
  Environmental, not a code defect — but it means the orchestrator-side gate tests were NOT
  re-run. They are untouched by this change (no file under `master_orchestrator` or
  `agent_core` was modified), so the risk is low rather than zero.

### Limitations recorded, not defects

- L-1 (A2): the suite stubs the judge everywhere, so what is proven is that an `ID_NUMBER`
  finding flows correctly and that the prompt asks for one. Whether a given model complies on
  an identifier format it has never seen is not provable here. This is inherent to PLAN D7's
  choice of mechanism and is already recorded as PLAN R-5.
- L-2: `pii.leaked_types` is the deterministic scanner, so an `ID_NUMBER` masked on the way in
  is not re-checked on the way out — the same gap that already exists for `PERSON` and
  `LOCATION`, and named as such in its docstring. The output path is not unguarded: the judge
  runs on it too and `_mask_model_pii` applies there. Worth a follow-up task, not a blocker.

### Repo-state issue found while validating (NOT caused by this task)

- V-1 (blocking a commit, not the task): the git index holds a staged rename of the entire
  `tasks/` tree from `.claude/tasks/` to `tasks/`, left over from the earlier layout
  experiment, while the working tree has `.claude/tasks/` back and untracked. Committing as-is
  would record the deletion of the whole task archive. Nothing is lost — it is index-only and
  HEAD still has everything — but it must be undone before any commit: `git reset` (unstage),
  then confirm `git status` shows only the three modified `mcp/guardrails` files plus the new
  `test_prompt_contract.py`. Deliberately NOT written into `open_issues`: it is a repository
  state defect, not an unmet requirement of this task.
