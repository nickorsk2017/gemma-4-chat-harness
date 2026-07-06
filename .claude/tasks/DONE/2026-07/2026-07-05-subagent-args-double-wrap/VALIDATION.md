# VALIDATION — 2026-07-05-subagent-args-double-wrap
## v1 — PASS
A1: _shape_args unit-tested (AST-extracted, no heavy imports): all 4 schema/shape combos
correct + non-dict guard; file compiles. Root cause from user's mcp logs (double-wrapped
{'request': {'request': ...}}) is no longer producible.
