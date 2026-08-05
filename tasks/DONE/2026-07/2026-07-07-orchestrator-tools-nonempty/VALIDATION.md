# VALIDATION — 2026-07-07-orchestrator-tools-nonempty

## v1 — PASS
- A1 PASS: stubbed SubagentToolset.load(), 3 cases —
  ['search_web','analyze_document'] -> prints count+names+schema, "PASS", exit 0;
  ['analyze_document'] -> "required tool 'search_web' missing", exit 1;
  [] -> "tool list is EMPTY", exit 1.
- A2 PASS: empty list and missing search_web both -> stderr + exit 1 (above).
  Import/load failure path also verified: live run with agent deps absent prints
  "cannot import SubagentToolset (...)" and exits 1 (no traceback).
- py_compile OK. No LLM call. Single file, no new deps -> LOW confirmed.
- Live discovery run (real sub-agent spawn) left to Engineer: from mcp/ with the
  fleet installed, `python3 scripts/tools_check.py` — exit 0 confirms
  loaded.tools is non-empty and search_web is bound at the bind_tools() call.
