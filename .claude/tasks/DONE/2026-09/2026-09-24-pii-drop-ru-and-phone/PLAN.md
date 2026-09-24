# PLAN — 2026-09-24-pii-drop-ru-and-phone

## v1
### Impact map
| File | Change | Req |
|---|---|---|
| mcp/guardrails/detectors/pii.py | drop RU_ENTITIES, PHONE_NUMBER from entity lists; drop passport/phone/SNILS/INN patterns, recognizers, `valid_snils`, `valid_inn`; refresh module docstring and comments that name them (overlap comment, `_scan` docstring, phone-anchor comment) | R1, R2 |
| mcp/guardrails/__tests__/fixtures/corpus.py | PII_CASES keeps EMAIL, CARD, IBAN only; drop SNILS/INN comment line | R4 |
| mcp/guardrails/__tests__/test_pii.py | drop SNILS/INN checksum tests; drop SNILS/INN rows from false-positive table; leak test -> EMAIL_ADDRESS; two-types test -> EMAIL + CREDIT_CARD; add A1 negative test for the four removed forms | R4, A1 |
| mcp/guardrails/__tests__/test_pipeline.py | phone-based input, output-leak, medical, notice-merge and deterministic-type tests re-pointed to an email or card value; RU-type test renamed to a kept-type test | R4 |
| mcp/__tests__/test_guardrail_gates.py, mcp/__tests__/test_doc_analyzer_gate.py | stubbed Redaction type PHONE_NUMBER -> EMAIL_ADDRESS (plumbing tests, type string only) | A4 |
| mcp/guardrails/services/pipeline.py | docstring example "phone number or a passport" -> kept types | A4 |
| mcp/guardrails/schemas/verdict.py | Field description example 'PHONE_NUMBER' -> 'EMAIL_ADDRESS' | A4 |
| README.md | Guardrails section: structured PII list = email, credit card, IBAN | A4 |

### Sequence
1. pii.py (R1, R2).
2. Fixtures, then test_pii.py, then test_pipeline.py, then gate tests.
3. Docstrings, schema description, README.
4. grep for removed names outside task archive (A4); run mcp pytest (A5).

### Decisions
- D1: Overlap resolution in `redact` stays: email/card/IBAN can still collide.
- D2: `valid_luhn`/`valid_iban` and checksum promotion in `_scan` unchanged (R2).
- D3: Medical-path test keeps its intent (redaction survives clinical topic) using an email.

### Risks
- K1: Phone numbers now reach the answering LLM and the thread store in clear text; the
  judge prompt does not list phones, so only an "OTHER" report would catch one. Accepted by
  Engineer per TASK Notes; flagged for approval.
- K2: RU passport/SNILS/INN now rely solely on the judge's ID_NUMBER path; judge outage
  remains fail-closed (C2), so no silent pass-through on failure.
