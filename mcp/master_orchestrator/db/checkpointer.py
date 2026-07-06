"""Thread-memory checkpointer lifecycle (LangGraph persistence).

PostgreSQL (``AsyncPostgresSaver`` over a psycopg async pool) when
``ORCHESTRATOR_DATABASE_URL`` is set; otherwise an in-process ``InMemorySaver``
so local/stdio dev runs with no database. Built lazily inside the running event
loop (async savers must not be constructed at import time) and exactly once per
process; ``setup()`` creates the checkpoint schema idempotently.
"""

from __future__ import annotations

import asyncio
from typing import Any

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver

from master_orchestrator.config import settings

_saver: BaseCheckpointSaver | None = None
_pool: Any = None  # keep the pool referenced for the process lifetime
_lock = asyncio.Lock()


async def _build_postgres_saver(url: str) -> BaseCheckpointSaver:
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    from psycopg.rows import dict_row
    from psycopg_pool import AsyncConnectionPool

    global _pool
    _pool = AsyncConnectionPool(
        url,
        open=False,
        # Required by AsyncPostgresSaver: autocommit + dict rows, no prepared
        # statement cache (pgbouncer-safe).
        kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row},
    )
    await _pool.open()
    saver = AsyncPostgresSaver(_pool)
    await saver.setup()
    return saver


async def get_checkpointer() -> BaseCheckpointSaver:
    """Return the process-wide checkpointer, building it on first use."""
    global _saver
    if _saver is not None:
        return _saver
    async with _lock:
        if _saver is None:
            if settings.database_url:
                _saver = await _build_postgres_saver(settings.database_url)
            else:
                _saver = InMemorySaver()
    return _saver


async def close_checkpointer() -> None:
    """Release the Postgres pool (tests / graceful shutdown)."""
    global _saver, _pool
    if _pool is not None:
        await _pool.close()
    _saver = None
    _pool = None
