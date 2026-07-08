# VALIDATION — 2026-07-07-memory-update-as-node

## v1 — PASS
- A1 PASS: save() -> aupdate_state(..., as_node=_MEMORY_NODE); the constant is the
  single source used by add_node and both edges; the only "noop" literal left is
  the constant definition (grep-confirmed).
- A2 PASS: memory.py py_compiles clean; no new deps; load/delete unchanged.
- Live confirmation left to Engineer (needs Postgres + langgraph): a chat turn now
  reaches save() and persists without "Ambiguous update, specify as_node", and a
  follow-up turn reloads prior history.
