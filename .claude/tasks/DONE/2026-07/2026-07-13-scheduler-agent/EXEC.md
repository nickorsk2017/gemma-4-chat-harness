# EXEC — 2026-07-13-scheduler-agent

## v1

Implemented per PLAN v1 (P1-P11). New self-contained MCP dist `mcp/scheduler_agent/`;
orchestrator/compose/env/README wired for standalone registration only (no loop edits).

### Created (scheduler_agent dist)
- P1 schemas/scheduling.py — EventStatus, Intent, `Event` (UTC), `SchedulerDecision`.
      schemas/http.py — `ScheduleRequest{thread_id,time_local,prompt,file?}`,
      `ScheduleResult{thread_id,intent,message,event?}`, `ScheduleResponse` alias.
- P2 config.py — SchedulerAgentSettings (env_prefix SCHEDULER_AGENT_): transport,
      database_url (None-default so import stays clean, A1), llm_* from agent_core.
- P3 db/models.py — SQLAlchemy `Event` ORM -> table `events` exactly per R6 (Uuid pk,
      unique thread_id, scheduled_at TIMESTAMPTZ, timezone, status, created/updated_at).
      db/session.py — async engine (`postgresql+psycopg://`), sessionmaker, init_db
      (create_all), async_url/sync_url normalizers, DatabaseConfigError if URL missing.
      db/repository.py — EventRepository.get_by_thread / upsert (create-or-replace by
      thread_id) / set_status; returns Pydantic domain, never ORM rows.
- P4 services/runtime.py — module AsyncIOScheduler (UTC) + SQLAlchemyJobStore on same DB;
      schedule_event/cancel_job keyed `event:<thread_id>`; module-level async `fire_event`
      flips status->completed (serializable job ref). Lazy start guarded.
- P5 prompts/schedule.py — SCHEDULE_DECISION: JSON-only decision, relative dates anchored
      to time_local, clarify/reject/create/update/cancel rules.
- P6 services/scheduler_service.py — `handle`: ensure_ready(init_db+scheduler) -> load
      existing -> ONE Gemma call -> strict SchedulerDecision (fail-soft to clarify) ->
      `_apply`. clarify/reject = no DB, no job (R4,R9). create/update: `_parse_local`
      converts offset-aware local -> UTC, past-check vs time_local-derived now (R5,R9),
      DB upsert BEFORE APScheduler register (R7 re-derivable). cancel: status=cancelled +
      remove job. Always returns assistant `message` (R8).
- P7 tools/schedule.py — thin `manage_schedule(request)` -> service -> agent_core envelope,
      fail-soft (R7). Receives request UNMODIFIED (R2).
- P8 main.py — FastMCP("scheduler_agent"), registers tool; DB+scheduler init lazily.
- P9 pyproject.toml — dist `scheduler-agent`, script `scheduler-agent`, deps: fastmcp,
      langchain-core, pydantic(+settings), sqlalchemy[asyncio], psycopg[binary],
      apscheduler<4, agent-core. Flat hatch layout like siblings.

### Modified (fleet wiring, P10 / R10)
- master_orchestrator/config.py — added scheduler_agent stdio spec to DEFAULT_SUBAGENTS.
- mcp/pyproject.toml — added scheduler-agent to dev aggregator + uv sources.
- docker-compose.yml — mcp service gets SCHEDULER_AGENT_DATABASE_URL (shared postgres).
- mcp/.env.example — documented SCHEDULER_AGENT_DATABASE_URL.
- mcp/README.md — scheduler_agent added to agent + package tables.

### Verification (P11)
- `python -m py_compile` on all new modules + modified orchestrator config: PASS.
- Pure-logic tests (no third-party deps available; sandbox offline for pip):
  * A2 time math: 2026-07-14T16:00-03:00 -> 2026-07-14T19:00:00Z (astimezone UTC). PASS.
  * past-check uses time_local-derived now (not server clock). PASS.
  * _extract_json tolerant of plain/fenced/prose-wrapped JSON. PASS.
  * async_url/sync_url normalize postgres/postgresql/+psycopg URLs to psycopg3. PASS.
- Not run: live import of full stack + real Postgres (fastmcp/sqlalchemy/apscheduler not
  installable offline in sandbox). Contract/pattern conformance checked against
  web_agent/doc_analyzer templates.

### Notes / known limitations
- Standalone registration only: orchestrator tool-loop is not modified to inject
  time_local/thread_id into tool args (per Engineer decision). The tool contract carries
  those fields (R2); end-to-end forwarding wiring is deferred.

## v2 — fix I1 (logic)
- mcp/Dockerfile:17 — added `./scheduler_agent` to the pip install line (before
  master_orchestrator, after agent_core); header comment updated to "four sub-agents".
  Deployed image now contains the module the orchestrator spawns over stdio (R10, A1/A5).
