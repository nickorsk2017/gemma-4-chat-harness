# EXEC — 2026-07-07-memory-update-as-node

## v1
master_orchestrator/services/memory.py:
- Added constant `_MEMORY_NODE = "noop"` with a comment on why explicit as_node
  is required.
- _build_graph now uses _MEMORY_NODE for add_node + both edges.
- save() passes `as_node=_MEMORY_NODE` to aupdate_state, resolving the ambiguous
  authoring-node inference. load()/delete() untouched.
py_compile OK.
