# TASK — 2026-07-13-scheduler-event-ids
owner: Engineer
immutable: true

## Context
Builds on the shipped scheduler_agent. `thread_id` stands in for `user_id` (chat has no
auth/registration), so one thread may own MANY scheduled events. Each event must have its
own identifier independent of thread_id.

## Requirements
- R1: `events.thread_id` is NO LONGER unique — it groups all events belonging to one
  conversation/user (indexed, non-unique). Each event keeps its own `id UUID` primary key,
  which is the canonical task identifier.
- R2: Creating a schedule ALWAYS inserts a NEW event with a freshly generated `id` (no more
  upsert-by-thread / one-event-per-thread). The assistant reply and `ScheduleResult.event`
  expose that `id` so the client can reference the task later (status/cancel from outside
  the chat).
- R3: The APScheduler job identifier is derived from the EVENT id (not thread_id): one job
  per event, keyed by the event's own `id`. Fire/cancel/reschedule operate per event id.
- R4: Update, cancel, and status/details operations target a SPECIFIC event via `event_id`
  supplied by the user (parsed from the prompt by the LLM into the decision). Every such
  op is scoped to the request's `thread_id` (a user may only act on their own events).
- R5: If the user asks to update/cancel/get-status but provides NO `event_id` (or an id not
  found for this thread), the agent does NOT mutate anything and returns a clarifying reply
  asking for the event id. (No DB write, no APScheduler change.)
- R6: Add a status/details capability: given a valid `event_id` for the thread, return the
  event's stored details (title, time in UTC, status) as the assistant message + in
  `ScheduleResult.event`.
- R7: All prior guarantees remain: time_local is the only clock; store/schedule in UTC;
  Postgres is source of truth; clarify/reject never write; fail-soft envelope; message
  always returned for the thread.

## Acceptance
- A1: Two consecutive "schedule ..." requests on the SAME thread_id create TWO rows with
  distinct `id`s, both persisted, each with its own APScheduler job keyed by its id.
- A2: `ScheduleResult.event.id` is returned on create/update/status so the client can
  address the task independently of thread_id.
- A3: Cancel with a valid event_id sets THAT event's status=cancelled and removes its job,
  leaving the thread's other events untouched.
- A4: Update/cancel/status with a missing or unknown event_id returns a clarifying question
  and makes no DB/APScheduler change.
- A5: A cancel/update/status event_id belonging to a DIFFERENT thread is treated as
  not-found (scoped by thread_id) -> clarify, no change.
- A6: schema: events.thread_id index is non-unique; events.id remains PK.

## Constraints
- Harness precedence; contracts-first; thin tools; config-not-constants; no mock LLM.
- Standalone sub-agent (no orchestrator loop changes).
- Backward note: this changes the `events` uniqueness; acceptable (create-on-startup schema,
  no migration framework) — document that an existing unique index must be dropped if a DB
  was already initialised.
