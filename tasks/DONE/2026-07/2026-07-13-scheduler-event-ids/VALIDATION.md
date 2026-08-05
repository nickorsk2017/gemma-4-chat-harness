# VALIDATION — 2026-07-13-scheduler-event-ids

## v1 — PASS

Independent review (subagent) + compile + pure-logic mirrors against TASK R1-R7 / A1-A6.

PASS with file-level evidence:
- R1/A6: db/models.py — thread_id non-unique index; id UUID PK.
- R2/A1/A2: repository.create always inserts a new uuid row (no upsert); service CREATE ->
  repo.create; ScheduleResult.event (with id) returned on create/update/status.
- R3: runtime job key `event:<event_id>`; schedule/cancel/fire use event_id; fire ->
  repo.complete(event_id).
- R4/A3/A5: update/cancel/status resolved via _target -> get_for_thread (id AND thread_id
  scoped); cross-thread/unknown id -> None -> clarify, no mutation.
- R5/A4: missing/unknown/garbage id -> _need_id clarify BEFORE any DB/APScheduler call.
- R6: status returns title/UTC-time/status in message + event.
- R7: time_local sole clock; UTC store/schedule; clarify/reject no writes; fail-soft
  envelope; message always present.
Consistency: no leftover upsert/get_by_thread; prompt placeholders match .format keys;
unused EventStatus import removed from runtime.

Findings were low/trivial only (theoretical TOCTOU assert; empty-message edge on cancel;
one stale docstring). All three folded into EXEC v2 (assert removed -> graceful clarify;
default messages added; http.py thread_id description fixed). Re-compiled: PASS.

Migration caveat (real, documented EXEC): an already-initialised DB must drop the old UNIQUE
index/constraint on events.thread_id manually (create_all won't alter it); fresh DBs fine.

Verdict: PASS. R1-R7 and A1-A6 met (live end-to-end with real Postgres/LLM not runnable in
the offline sandbox; contracts, scoping and wiring verified by review + compile + logic).
