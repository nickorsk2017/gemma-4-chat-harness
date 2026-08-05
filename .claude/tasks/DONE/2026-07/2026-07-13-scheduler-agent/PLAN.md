# PLAN — 2026-07-13-scheduler-agent

## v1

### Architecture (satisfies R1,R2,R3)
New self-contained MCP dist `mcp/scheduler_agent/` (import root `scheduler_agent`),
sharing only `agent_core`. One MCP tool `manage_schedule` receives the raw request
(thread_id, time_local, prompt, optional file) unmodified and owns all logic. Layering:
tool (thin: validate->service->envelope) -> service (orchestration of LLM reasoning +
persistence + APScheduler) -> db (SQLAlchemy async repo) + scheduler runtime (APScheduler)
+ prompts (LLM instructions) + schemas (Pydantic contracts). Mirrors web_agent/doc_analyzer
patterns; no import of any sibling agent.

### Reasoning flow (R3,R4,R9) — LLM-driven, single structured pass
service.handle(request):
1. Load current event for thread_id from DB (context for update/cancel intents).
2. One Gemma call: prompt embeds `time_local` as the authoritative "now", the user prompt,
   and (if present) the existing event; instructs the model to return a strict JSON decision:
   intent in {create, update, cancel, clarify, reject}, plus title, description,
   scheduled_at_local (ISO-8601 w/ same offset as time_local), past_ok flag, and a
   human-friendly `message`. All natural-language date math is the model's job, anchored to
   time_local (never server clock).
3. Parse/validate the JSON into a Pydantic `SchedulerDecision` (fail-soft: on unparseable
   output, fall back to a clarify message). This is the boundary that keeps intent =
   deterministic downstream.

### Decision handling (R4,R5,R6,R7,R8,R9)
- clarify  -> return message only; NO db row, NO job. (R4,A3)
- reject   -> return message only; NO db row, NO job. (R9,A4)
- create/update: post-validate scheduled_at_local: parse offset-aware datetime; convert to
  UTC (`astimezone(timezone.utc)`); enforce not-in-past unless past_ok (R9); on failure ->
  reject message. Persist row (UTC scheduled_at, original tz string, status=scheduled) via
  repo.upsert keyed by thread_id; then (re)register APScheduler DateTrigger job id=thread_id
  in UTC that flips status->completed on fire. DB write precedes job registration; job is
  re-derivable from the row (DB authoritative, R7,A5).
- cancel: mark row status=cancelled, remove APScheduler job if present; return confirmation.
- Every branch returns an assistant `message` string surfaced in the envelope (R8,A6).

### Time handling detail (R5)
`time_local` is the only clock. Model emits local ISO; service converts to UTC for all
storage/scheduling. `timezone` column stores the offset/zone from time_local for display.
No use of datetime.now()/server tz in the parsing path.

### Data & schema (R6)
`db/models.py`: SQLAlchemy `Event` ORM (declarative) -> table `events` exactly per R6
(UUID pk default uuid4, thread_id, title, description, scheduled_at TIMESTAMPTZ, timezone,
status, created_at, updated_at server-defaulted/updated). `db/session.py`: async engine +
sessionmaker from config.database_url (psycopg async driver). `db/repository.py`:
EventRepository with get_by_thread, upsert(create/update by thread_id), set_status. `init_db`
creates the table on startup (metadata.create_all) — additive, no migration framework.

### Scheduler runtime (R7)
`services/runtime.py`: module-level AsyncIOScheduler started lazily on first use; jobstore =
SQLAlchemyJobStore on config.database_url (APScheduler persists its own job table, separate
from `events`; DB `events` remains the source of truth). Helper schedule_event(thread_id,
run_at_utc) / cancel_job(thread_id). Fire callback marks the event completed via repo.

### Files to create (module map, satisfies R1)
- scheduler_agent/__init__.py
- scheduler_agent/config.py            (SchedulerAgentSettings: transport, database_url,
                                        llm_*; env_prefix SCHEDULER_AGENT_)
- scheduler_agent/schemas/__init__.py
- scheduler_agent/schemas/scheduling.py (Event domain model, SchedulerDecision, EventStatus)
- scheduler_agent/schemas/http.py       (ScheduleRequest{thread_id,time_local,prompt,file?},
                                        ScheduleResult{message,event?,intent}; AgentResponse aliases)
- scheduler_agent/prompts/__init__.py
- scheduler_agent/prompts/schedule.py   (SCHEDULE_DECISION system/task prompt template)
- scheduler_agent/db/__init__.py
- scheduler_agent/db/models.py          (SQLAlchemy Event ORM + Base)
- scheduler_agent/db/session.py         (async engine/sessionmaker + init_db)
- scheduler_agent/db/repository.py      (EventRepository)
- scheduler_agent/services/__init__.py
- scheduler_agent/services/runtime.py   (APScheduler runtime)
- scheduler_agent/services/scheduler_service.py (handle(): reasoning+persist+schedule)
- scheduler_agent/tools/__init__.py
- scheduler_agent/tools/schedule.py     (register manage_schedule tool)
- scheduler_agent/main.py               (FastMCP server; init_db + start scheduler)
- scheduler_agent/pyproject.toml        (dist scheduler-agent; console script scheduler-agent)

### Files to modify (R10)
- mcp/master_orchestrator/config.py : add scheduler_agent to DEFAULT_SUBAGENTS (stdio spec).
- mcp/pyproject.toml                : add scheduler_agent editable to dev aggregator.
- docker-compose.yml                : add SCHEDULER_AGENT_DATABASE_URL to mcp service env
  (reuse postgres); note apscheduler jobstore uses same DB.
- mcp/.env.example                  : document SCHEDULER_AGENT_DATABASE_URL (+ default).
- mcp/README.md (optional)          : mention scheduler_agent in the agent table.

### Sequencing (Executor order)
P1 schemas (contracts first) -> P2 config -> P3 db (models,session,repository) ->
P4 runtime (APScheduler) -> P5 prompts -> P6 service (LLM reasoning + decision handling) ->
P7 tool -> P8 main.py -> P9 pyproject -> P10 orchestrator/compose/env wiring ->
P11 local import/syntax smoke check.

### Risks / mitigations
- LLM JSON drift -> strict Pydantic parse w/ clarify fallback; low temperature; explicit
  JSON-only instruction with schema in prompt.
- Async DB driver mismatch -> use SQLAlchemy async URL `postgresql+psycopg://` (psycopg3),
  APScheduler SQLAlchemyJobStore uses sync URL `postgresql+psycopg://` too (psycopg3 sync).
- APScheduler event loop -> AsyncIOScheduler must attach to the running MCP loop; start lazily
  inside async context, guard double-start.
- past-date false positives across tz -> compare in UTC using time_local-derived now, not
  server now.
- Scope creep into orchestrator loop -> registration only (R10 constraint), no loop edits.

### Acceptance mapping
A1:P1-P9  A2:P3,P6  A3:P6(clarify)  A4:P6(reject)  A5:P3,P4,P6  A6:P6,P7  A7:P1,P6,P7
