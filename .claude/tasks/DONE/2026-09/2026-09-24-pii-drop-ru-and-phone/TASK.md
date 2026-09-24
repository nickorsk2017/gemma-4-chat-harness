# TASK — 2026-09-24-pii-drop-ru-and-phone
owner: Engineer
immutable: true

## Requirements
- R1: The deterministic PII layer (`mcp/guardrails/detectors/pii.py`) stops detecting
  PHONE_NUMBER, RU_PASSPORT, RU_SNILS and RU_INN. Their recognizers, patterns and
  checksum validators are removed, not disabled by config.
- R2: The deterministic layer keeps detecting EMAIL_ADDRESS, CREDIT_CARD (Luhn) and
  IBAN_CODE (mod-97) with unchanged patterns, scores and entity names.
- R3: The model (judge) PII layer is out of scope: prompt and `_MODEL_PII_TYPES` are
  unchanged.
- R4: Tests, fixtures and documentation that name the removed types are updated so the
  suite describes the new detector set; no test is deleted merely to make the suite pass
  when its intent still applies to a kept type.

## Acceptance
- A1: `pii.redact` on text containing "+7 916 123-45-67", "45 05 № 123456",
  "112-233-445 95" or "500100732259" reports none of the removed types.
- A2: EMAIL_ADDRESS, CREDIT_CARD and IBAN_CODE cases from the corpus still redact, and the
  value is absent from the output.
- A3: Checksum false-positive guards for card and IBAN still pass.
- A4: No reference to the removed entity names or validators remains in source, tests or
  README (task archive excluded).
- A5: mcp pytest suite passes.

## Constraints
- C1: Supersedes 2026-08-05-pii-redaction-orchestration A4 (well-formed RU types resolve
  deterministically) for the removed types.
- C2: No new dependencies. Enforcement point and fail-closed policy unchanged.

## Notes
- Engineer decision: email stays; phone is removed entirely (all country codes), not only
  the RU leading-8 form.
