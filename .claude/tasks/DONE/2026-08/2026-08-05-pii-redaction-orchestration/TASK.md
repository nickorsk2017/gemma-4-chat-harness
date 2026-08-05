# TASK — 2026-08-05-pii-redaction-orchestration
owner: Engineer
immutable: true

## Requirements
- R1: Any personal identifier a user states MUST be masked before the text reaches the
  answering LLM and before it is written to the thread — irrespective of issuing country or
  format. RU passport, Spanish/Argentinian DNI, US SSN, a national ID card number, a
  document number in a format nobody enumerated: all in scope.
- R2: The enforcement point stays where it already is — the guardrails INPUT gate, called by
  `master_orchestrator` ahead of the tool loop and ahead of thread persistence. This task
  changes detection coverage, not placement.
- R3: Coverage for open-ended identifiers is decided at the LLM (judge) layer. Adding a regex
  per country is explicitly rejected as the mechanism: the set is unbounded and unknowable.
- R4: The deterministic pattern layer stays as the fast path for the well-formed types it
  already validates by checksum. It is not removed and not extended per country.
- R5: The judge prompt MUST stop excluding formatted identifiers from what it reports. Its
  current instruction not to list passports, phones, cards and similar assumes the
  deterministic layer already removed them; that assumption is false for any value that does
  not match a known format.
- R6: Masking uses typed placeholders. The type is what the output gate re-checks against, so
  it is load-bearing and is not collapsed to a single flat marker.
- R7: Reverse substitution stays out of scope: restoring a value requires storing it.
- R8: Guardrails failure or timeout on the input path stays fail-closed.
- R9: Raw identifier values are never logged, at any level.

## Acceptance
- A1: "Мой паспорт 44432423 и мой телефон 353536" — both values masked in the LLM payload and
  in the thread record. A follow-up asking for the passport number cannot be answered.
- A2: The same holds for a Spanish DNI ("mi DNI es 12345678Z") and a US SSN.
- A3: Ordinary numbers that are not personal identifiers — an order id, a year, a price, a
  version — are not masked.
- A4: Well-formed RU types still resolve through the deterministic layer with their existing
  entity names, not as a generic identifier.
- A5: With the judge unavailable, an input turn carrying an identifier is refused, not passed.
- A6: Latency: no additional model call is introduced — the judge already runs on every input
  turn. PLAN.md records the measured delta against the turn budget.

## Constraints
- C1: Enforcement point is fixed (R2). Redaction in the gateway or the frontend is not planned.
- C2: End-to-end turn budget is `master_orchestrator/config.py::turn_budget_s = 60.0`. The
  config is normative; the earlier 66 s figure is withdrawn. This task does not change the
  budget — it must not make the turn slower.
- C3: Parallel sub-agent dispatch is preserved.
- C4: No per-country regex zoo (R3).

## Notes
- Russian and Spanish user text in A1/A2 is verbatim test input, not prose.
