# EXEC — 2026-07-13-scheduler-event-ids

## v1

Delta on scheduler_agent per PLAN v1 (P1-P7). Identifier model: thread_id (user proxy,
non-unique) groups many events; each event's own UUID `id` is the task key + job key.

### Modified
- P1 schemas/scheduling.py — Intent += STATUS; SchedulerDecision += `event_id: str|None`
  (target event for update/cancel/status).
- P2 db/models.py — thread_id now `index=True` non-unique (dropped unique); id stays UUID PK.
  Docstring updated (thread_id == user proxy).
- P3 db/repository.py — replaced upsert-by-thread with id-centric ops (all return domain):
  create (new uuid row), get_for_thread (scoped), list_active_for_thread, update (scoped),
  set_status (scoped, user op), complete (id-only, for fire callback). `_as_uuid` guards
  bad/None ids -> None (=> not found => clarify). Cross-thread id -> None (A5).
- P4 services/runtime.py — job key = `event:<event_id>`; schedule_event/cancel_job/fire_event
  take event_id; fire_event -> repo.complete(event_id). Removed now-unused EventStatus import.
- P5 prompts/schedule.py — context is the thread's ACTIVE EVENTS list (id/title/utc); rules:
  update/cancel/status must carry a listed event_id; missing/unknown id -> clarify; create
  never reuses an id.
- P6 services/scheduler_service.py — handle loads list_active_for_thread; _reason feeds the
  list as JSON. _apply routes: clarify/reject (no write); STATUS/CANCEL/UPDATE require a
  scoped event via `_target` else `_need_id` clarify (no write, A4/A5); CREATE always
  repo.create (new id, A1); UPDATE repo.update + reschedule; CANCEL set_status cancelled +
  cancel_job (A3); all set ScheduleResult.event so id is returned (A2/R6). Time/UTC/past
  path unchanged (R7).

### Not changed
- schemas/http.py — ScheduleResult already carries `event` (with id) + intent; STATUS flows
  through the existing `intent` field. No request-shape change (event_id is parsed from the
  raw prompt by the LLM; standalone constraint honoured).
- No orchestrator/compose/Docker changes (already wired last task).

### Verification (P7)
- py_compile all 6 changed modules: PASS.
- prompt placeholders {time_local,active_events,prompt} == .format() keys: PASS.
- pure-logic mirrors (deps offline): _as_uuid None/garbage->None(clarify), valid->UUID;
  cross-thread id -> not found (A5); two creates -> distinct ids (A1). PASS.
- Not run: live import/full stack + real Postgres (fastmcp/sqlalchemy/apscheduler not
  installable offline).

### Migration note (R1 constraint)
create_all does NOT drop a pre-existing UNIQUE index on events.thread_id. For a DB already
initialised by the previous version, drop it manually once:
  ALTER TABLE events DROP CONSTRAINT IF EXISTS events_thread_id_key;
  DROP INDEX IF EXISTS ix_events_thread_id;  -- then it is recreated non-unique
Fresh databases are unaffected.

## v2 — review hardening (low findings from validation)
- scheduler_service._create_or_update: removed `assert event is not None`; UPDATE now
  returns a clarify if the scoped row vanished between resolve and update (no 500).
- Added default confirmation messages for create/update and cancel when the LLM returns an
  empty `message` (no empty assistant replies).
- schemas/http.py: corrected `thread_id` field description (user/conversation key, not event
  id) to match the new identifier model.
- py_compile PASS.
