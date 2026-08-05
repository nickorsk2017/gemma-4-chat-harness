# PLAN — 2026-07-07-memory-update-as-node

## v1

### Cause
memory.py compiles a 1-node no-op graph ("noop") purely to expose the Postgres
checkpointer's thread-keyed state. The graph is NEVER executed (no ainvoke); the
store only calls aget_state (read) and aupdate_state (write). aupdate_state with
as_node=None makes LangGraph infer the authoring node from the checkpoint's run
history — but no node ever ran, so inference is ambiguous ->
InvalidUpdateError("Ambiguous update, specify as_node"). Surfaced now because the
90s LLM timeout lets the turn reach save() instead of failing earlier at 45s.

### Fix (memory.py only)
- Add module constant `_MEMORY_NODE = "noop"`.
- Use it in `_build_graph` (`graph.add_node(_MEMORY_NODE, ...)`, edges).
- In `save()` pass `as_node=_MEMORY_NODE` to aupdate_state.

Attributing the write to "noop" is unambiguous and, since noop's only out-edge is
END, leaves the checkpoint with no pending task (next is empty) — a clean,
readable-back state. as_node=START was rejected: it would leave "noop" pending in
`next`.

### Validation
py_compile memory.py; static check that the constant is used in both add_node and
aupdate_state and that as_node is now passed. Live confirmation (a chat turn
persists + reloads without error) left to Engineer (needs Postgres + langgraph).
