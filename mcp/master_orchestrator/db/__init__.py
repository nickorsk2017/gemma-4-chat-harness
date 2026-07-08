"""Thread persistence lives in ``master_orchestrator.services.memory``.

Memory is backed by a LangGraph checkpointer keyed by ``thread_id``: an
``AsyncPostgresSaver`` when ``ORCHESTRATOR_DATABASE_URL`` is set (durable across
restarts), otherwise an in-process ``MemorySaver``. This package is a placeholder
for any additional persistence helpers.
"""
