-- Task 2026-08-02-remove-scheduler-agent / R7
-- Drops the scheduler feature's storage. Run by the Engineer, NOT by the harness.
--
-- Back up first (irreversible — risk K5 in PLAN.md):
--   pg_dump -h localhost -U agent -d agent_chat -t events -t apscheduler_jobs \
--     -f scheduler_tables_backup_$(date +%F).sql
--
-- Then:
--   psql -h localhost -U agent -d agent_chat -f drop_scheduler_tables.sql
--
-- `events`           — scheduler_agent's source of truth (db/models.py, __tablename__ = "events").
--                      Indexes (PK, ix_events_thread_id) drop with the table. No custom enum
--                      type exists: `status` is a plain String column.
-- `apscheduler_jobs` — APScheduler SQLAlchemyJobStore's execution table, default name, same DB
--                      (services/runtime.py). Execution engine only, re-derivable, not a source
--                      of truth.
--
-- Not dropped: LangGraph checkpointer tables (checkpoints*, ORCHESTRATOR_DATABASE_URL) — they
-- belong to the orchestrator's thread memory and are out of scope.

BEGIN;

DROP TABLE IF EXISTS apscheduler_jobs;
DROP TABLE IF EXISTS events;

COMMIT;
