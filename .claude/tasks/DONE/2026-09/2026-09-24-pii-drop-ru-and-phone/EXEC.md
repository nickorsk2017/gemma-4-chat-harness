# EXEC — 2026-09-24-pii-drop-ru-and-phone

## v1
| File | Change | Plan ref |
|---|---|---|
| mcp/guardrails/detectors/pii.py | ENTITIES = EMAIL/CARD/IBAN; removed `valid_snils`, `valid_inn`, passport/phone/SNILS/INN patterns and recognizers; docstrings and overlap comment updated | step 1, D1, D2 |
| mcp/guardrails/__tests__/fixtures/corpus.py | PII_CASES reduced to EMAIL/CARD/IBAN | step 2 |
| mcp/guardrails/__tests__/test_pii.py | SNILS/INN checksum tests replaced by a parametrized negative test for the four removed forms (A1); leak test on email; two-types test on card+email; SNILS/INN false-positive rows dropped | step 2 |
| mcp/guardrails/__tests__/test_pipeline.py | five phone-based tests re-pointed to email or card; RU-type test renamed to structured-type test on card | step 2, D3 |
| mcp/__tests__/test_guardrail_gates.py, test_doc_analyzer_gate.py | stubbed type PHONE_NUMBER -> EMAIL_ADDRESS | step 2 |
| mcp/guardrails/services/pipeline.py, schemas/verdict.py, README.md | examples and PII list updated | step 3 |

- grep for removed names in source/tests/README: 0 hits.
- mcp pytest (Python 3.14, fresh venv): 240 passed, 4 skipped.
