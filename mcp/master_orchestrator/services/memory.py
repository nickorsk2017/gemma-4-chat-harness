"""Per-thread conversation memory backed by a LangGraph checkpointer.

We keep the manual Gemma tool-calling loop; LangGraph is used ONLY as the thread
store. Thread state (history + gateway-extracted document text) is persisted by
``thread_id`` through a LangGraph ``AsyncPostgresSaver`` checkpointer. Postgres is
the single source of thread data: ``ORCHESTRATOR_DATABASE_URL`` is REQUIRED and
there is no in-memory fallback — a missing URL raises ``MemoryConfigError``.

A trivial single-node graph is compiled purely to expose the checkpointer's
thread-keyed state via ``aget_state`` / ``aupdate_state`` — no orchestration logic
lives in it.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from master_orchestrator.config import settings


# The memory graph's single node. The graph is never run through the pregel loop
# (only aget_state/aupdate_state are used), so state writes must be attributed to
# this node explicitly via `as_node` — otherwise LangGraph cannot infer the
# authoring node and raises "Ambiguous update, specify as_node".
_MEMORY_NODE = "noop"


class MemoryConfigError(RuntimeError):
    """Thread memory is misconfigured (missing ORCHESTRATOR_DATABASE_URL)."""


@dataclass
class ThreadState:
    """Everything remembered for one conversation thread (loop-facing view)."""

    messages: list[dict[str, str]] = field(default_factory=list)  # {"role","text"}
    documents: dict[str, str] = field(default_factory=dict)  # name -> full text


class _GraphState(TypedDict):
    """Checkpointed channels. LastValue semantics: updates replace."""

    messages: list[dict[str, str]]
    documents: dict[str, str]


def _build_graph(checkpointer: Any):
    """Compile a no-op single-node graph used only for its checkpointed state."""
    graph = StateGraph(_GraphState)
    graph.add_node(_MEMORY_NODE, lambda state: {})
    graph.add_edge(START, _MEMORY_NODE)
    graph.add_edge(_MEMORY_NODE, END)
    return graph.compile(checkpointer=checkpointer)


class CheckpointThreadStore:
    """Thread memory read/written through a LangGraph checkpointer by thread_id."""

    def __init__(self, graph: Any) -> None:
        self._graph = graph

    @staticmethod
    def _cfg(thread_id: str) -> dict[str, Any]:
        return {"configurable": {"thread_id": thread_id}}

    async def load(self, thread_id: str) -> ThreadState:
        snapshot = await self._graph.aget_state(self._cfg(thread_id))
        values = snapshot.values or {}
        return ThreadState(
            messages=list(values.get("messages") or []),
            documents=dict(values.get("documents") or {}),
        )

    async def save(self, thread_id: str, state: ThreadState) -> None:
        messages = state.messages[-settings.history_max_messages :]
        await self._graph.aupdate_state(
            self._cfg(thread_id),
            {"messages": messages, "documents": state.documents},
            as_node=_MEMORY_NODE,
        )

    async def delete(self, thread_id: str) -> bool:
        cp = self._graph.checkpointer
        try:
            if hasattr(cp, "adelete_thread"):
                await cp.adelete_thread(thread_id)
            elif hasattr(cp, "delete_thread"):
                cp.delete_thread(thread_id)
            else:
                return False
            return True
        except Exception:  # noqa: BLE001 - deletion is best-effort, fail soft
            return False


_store: CheckpointThreadStore | None = None
_lock = asyncio.Lock()
# Kept alive for the process lifetime so the Postgres connection isn't closed.
_pg_ctx: Any = None


async def _build_checkpointer() -> Any:
    """Build the Postgres saver (set up once). No fallback: Postgres is required."""
    url = settings.database_url
    if not url:
        raise MemoryConfigError(
            "ORCHESTRATOR_DATABASE_URL is not set. Thread data is read from "
            "Postgres only; there is no in-memory fallback."
        )
    global _pg_ctx
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

    _pg_ctx = AsyncPostgresSaver.from_conn_string(url)
    saver = await _pg_ctx.__aenter__()
    await saver.setup()
    return saver


async def get_store() -> CheckpointThreadStore:
    """Lazily build the store once, inside the running event loop."""
    global _store
    if _store is not None:
        return _store
    async with _lock:
        if _store is None:
            checkpointer = await _build_checkpointer()
            _store = CheckpointThreadStore(_build_graph(checkpointer))
    return _store
