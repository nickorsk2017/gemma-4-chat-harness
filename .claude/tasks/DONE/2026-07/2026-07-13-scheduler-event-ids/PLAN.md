# PLAN — 2026-07-13-scheduler-event-ids

## v1

Delta on the shipped scheduler_agent. Identifier model shifts from "thread_id owns one
event" to "thread_id (=user) owns many events; event.id is the task key" (R1,R2,R3).

### Schema (R1,A6)
- db/models.py: `thread_id` -> `index=True, unique=False` (drop unique). `id` stays UUID PK
  (default uuid4). No other column change (title/description/scheduled_at UTC/timezone/
  status/timestamps unchanged).
- Migration note (constraint): create_all won't drop a pre-existing unique index. EXEC must
  document the manual drop for already-initialised DBs (R1 constraint in TASK).

### Repository (R2,R3,R4,R5,R6) — db/repository.py
Replace upsert-by-thread with id-centric ops, all returning Pydantic Event:
- create(thread_id, title, description, scheduled_at_utc, timezone) -> Event  (new uuid row)
- get_for_thread(event_id, thread_id) -> Event | None  (scoped fetch; None if wrong thread)
- update(event_id, thread_id, **fields) -> Event | None  (scoped; reset status=scheduled)
- set_status(event_id, thread_id, status) -> Event | None  (scoped)
Remove get_by_thread/upsert (or keep get_latest_active_for_thread only if needed — not
required by chosen semantics). All mutating ops are thread-scoped (A5).

### Runtime (R3) — services/runtime.py
- `_job_id(event_id)` -> f"event:{event_id}". schedule_event(event_id, run_at_utc),
  cancel_job(event_id), fire_event(event_id) mark THAT event completed. fire_event needs
  thread scoping? No — event_id is globally unique (UUID PK); set_status by id alone is safe
  for the fire callback. Add repo.set_status_by_id(event_id, status) OR keep thread-scoped
  variant for user ops + an unscoped id-only variant for the fire callback. Plan: repo gets
  `complete(event_id)` (id-only, used by fire_event) plus thread-scoped user ops.

### Decision contract (R4,R5,R6) — schemas/scheduling.py
- Intent enum: add `STATUS`. (create, update, cancel, clarify, reject, status)
- SchedulerDecision: add `event_id: str | None` (the id the user referenced, else null).

### Prompt (R4,R5,R6) — prompts/schedule.py
- Existing-event context becomes a LIST of the thread's active events (id + title +
  scheduled_at) so the model can echo ids and validate references.
- Instruct: update/cancel/status MUST carry the user-provided event_id in `event_id`; if the
  user wants update/cancel/status but gave no id -> intent "clarify" asking for the event id.
- create still needs date+time+subject else clarify.

### Service (R2..R7) — services/scheduler_service.py
- load thread's active events (repo.list_active_for_thread) -> feed prompt context.
- create: repo.create(...) -> new Event; runtime.schedule_event(event.id, utc); return
  event (with id) + confirmation incl. id (R2,A1).
- update: require decision.event_id; repo.get_for_thread(id,thread) None -> clarify (R5,A4,A5);
  else repo.update(...) + runtime.schedule_event(id,utc) (reschedule) -> event.
- cancel: require event_id; scoped fetch None -> clarify; else repo.set_status(id,thread,
  cancelled) + runtime.cancel_job(id) (A3).
- status: require event_id; scoped fetch None -> clarify; else return event details message
  + event (R6).
- clarify/reject: unchanged (no writes).
- _parse_local/time/UTC path unchanged (R7).

### http schema
- schemas/http.py: ScheduleResult already carries `event` (has id) + intent; add STATUS to
  the Intent import usage implicitly (enum extended). No request change — event_id is parsed
  from the prompt by the LLM (orchestrator forwards raw prompt, standalone constraint).

### Files
Modify: db/models.py, db/repository.py, services/runtime.py, services/scheduler_service.py,
prompts/schedule.py, schemas/scheduling.py. (schemas/http.py only if intent surface needs it.)
No new files. No orchestrator/compose/Docker changes (already wired).

### Sequencing
P1 schemas(Intent+event_id) -> P2 models(unique drop) -> P3 repository(id-centric) ->
P4 runtime(job=event id) -> P5 prompt(list+id rules) -> P6 service(branches) -> P7 compile+
pure-logic checks (two-creates-distinct-ids, scoped-not-found->clarify, job id derivation).

### Risks
- fire_event vs thread scoping: use id-only completion (UUID unique) to avoid needing
  thread in the serialized job args beyond event_id.
- LLM must not fabricate an event_id: prompt lists real ids; service re-validates via scoped
  fetch, so a hallucinated id -> not-found -> clarify (safe).
- Pre-existing unique index on thread_id in a live DB: documented manual drop (create_all
  won't alter it).

### Acceptance map
A1:P3,P6 A2:P1,P6 A3:P3,P4,P6 A4:P5,P6 A5:P3,P6 A6:P2
