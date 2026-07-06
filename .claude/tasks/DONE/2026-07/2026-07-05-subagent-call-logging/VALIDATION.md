# VALIDATION — 2026-07-05-subagent-call-logging
## v1 — PASS
A1: AST-extracted wrapper test — success emits INFO with duration, failure emits WARNING
with error text; file compiles.

## v2 (correction)
The v1 stub run crashed on the harness's own test double (AgentResponse[Any] subscript on
a naive stub) and the PASS above was recorded prematurely. Re-ran with a corrected double:
both assertions verified (INFO "ok in Xs" on success; WARNING "FAILED in Xs: <error>" on
failure). Production code unchanged — defect was in the test double only. PASS stands.
