# EXEC — 2026-07-07-orchestrator-tools-nonempty

## v1
Created mcp/scripts/tools_check.py (single file, no new deps). Reproduces the
orchestrator's binding step: awaits SubagentToolset.load() and inspects
loaded.tools (the list passed to bind_tools). Prints tool count + names and each
tool's args schema (pydantic v2/v1 tolerant via _schema_of). Fails (exit 1) on:
load exception, empty list, or search_web absent; PASS (exit 0) otherwise. No LLM
call. sys.path + PYTHONPATH prepend mcp/ so spawned stdio sub-agents import
cleanly without an editable install. py_compile OK.

## v2
Hardened: wrapped the `from master_orchestrator...` import in try/except so a
missing/broken agent package exits 1 with a readable message instead of an
uncaught traceback (surfaced by the live run in the deps-less sandbox).
py_compile OK.
