# TASK — 2026-07-07-memory-update-as-node
owner: Engineer
immutable: true

## Requirements
- R1: Fix "InvalidUpdateError: Ambiguous update, specify as_node" raised from
  CheckpointThreadStore.save() -> graph.aupdate_state(). The memory graph's node
  never runs through the pregel loop (only aget_state/aupdate_state are used), so
  LangGraph cannot infer which node the state update belongs to.
- R2: Attribute the checkpoint write explicitly to the memory node by passing
  `as_node=<node name>` to aupdate_state. Reference the node via a single shared
  constant so add_node() and aupdate_state() cannot drift.

## Acceptance
- A1: save() calls aupdate_state(..., as_node=<node>); node name is a shared
  constant used by _build_graph too.
- A2: memory.py py_compiles clean; no new deps; load/delete unchanged.

## Constraints
- Touch only master_orchestrator/services/memory.py.
