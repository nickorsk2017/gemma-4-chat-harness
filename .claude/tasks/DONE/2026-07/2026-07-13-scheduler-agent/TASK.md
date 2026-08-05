# TASK — 2026-07-13-scheduler-agent
owner: Engineer
immutable: true

## Requirements
- R1: Add a new MCP sub-agent `scheduler_agent` under `mcp/`, following mcp/CLAUDE.md
  folder structure (db/, schemas/, tools/, prompts/, config.py, main.py, own pyproject.toml)
  and the shared `agent_core` envelope. One responsibility: manage scheduled events.
- R2: Expose a single MCP tool that receives the user's request UNMODIFIED. Input contract:
  `{ thread_id: str, time_local: str (ISO-8601 w/ offset), prompt: str, file?: optional }`.
  The orchestrator forwards the raw request; the scheduler owns all scheduling logic.
- R3: Reasoning is Gemma-LLM-driven via `agent_core.llm.get_llm()` (no mock LLM). The LLM
  parses intent, extracts title/description/datetime, and decides whether required info is
  missing. Relative dates (today/tomorrow/next Monday/in 2 hours/next month) are interpreted
  EXCLUSIVELY from `time_local`, never server time.
- R4: Clarifying questions — if required info (date and/or time and/or subject) is missing,
  do NOT create/update an event or an APScheduler job; return a human-friendly clarifying
  question as the assistant reply.
- R5: Time handling — interpret relative dates using `time_local`, convert the final datetime
  to UTC, persist UTC in Postgres, and register APScheduler jobs using UTC. Never use the
  local timezone internally after parsing.
- R6: Persistence — real Postgres via SQLAlchemy (async). Table `events` with columns:
  id UUID, thread_id TEXT, title TEXT, description TEXT, scheduled_at TIMESTAMPTZ,
  timezone TEXT, status TEXT (scheduled|completed|cancelled), created_at, updated_at.
  Postgres is the single source of truth.
- R7: Scheduling engine — APScheduler (AsyncIO) is the EXECUTION engine only, using UTC.
  `thread_id` is the event/job identifier (one scheduling conversation per thread).
  Create/update/cancel the APScheduler job to mirror the DB; DB is authoritative, APScheduler
  is not permanent storage.
- R8: Every assistant reply the scheduler produces (clarification, scheduling confirmation,
  validation error, update confirmation, cancellation confirmation) is returned in the tool
  result so it can be stored in the chat thread. The scheduler PRODUCES the assistant message.
- R9: Validation — reject impossible/invalid requests (invalid date, past date unless
  explicitly requested, impossible time) with a human-friendly explanation; no DB row or job
  is created for rejected requests.
- R10: Wire the sub-agent into the fleet: register in master_orchestrator config (standalone
  sub-agent registration only — no changes to the orchestrator tool-calling loop), add its
  DB URL / settings to docker-compose + .env.example, add its dependency install to the mcp
  dev aggregator.

## Acceptance
- A1: `scheduler_agent` package imports cleanly and its `main.py` builds a FastMCP server
  exposing the scheduling tool; folder structure and agent_core usage match mcp/CLAUDE.md.
- A2: A request with enough info (e.g. "Schedule a meeting tomorrow at 4 PM",
  time_local=2026-07-13T18:00:00-03:00) parses to 2026-07-14 16:00 local -> stored/scheduled
  as 2026-07-14T19:00:00Z (UTC), status=scheduled, and returns a confirmation message.
- A3: A request missing info (e.g. "Schedule a meeting") returns a clarifying question and
  creates NO DB row and NO APScheduler job.
- A4: An invalid/past request returns a human-friendly rejection and creates no DB row/job.
- A5: Events persist in Postgres in UTC; APScheduler jobs are keyed by thread_id in UTC; the
  DB is the source of truth (job re-derivable from the row).
- A6: The tool always returns an assistant message string in its envelope for thread storage.
- A7: All tools stay inside the agent_core fail-soft envelope (no exception crosses the MCP
  boundary); domain models are Pydantic; prompts live in prompts/; config in config.py.

## Constraints
- Follow precedence: `.claude/` harness > root CLAUDE.md > subsystem mcp/CLAUDE.md.
- Contracts first (schemas/*.py before tools); tools are thin (validate -> service -> envelope).
- Config, not constants: DB URL, model, timeouts from config.py (env-backed); no secrets.
- No mock LLM (Gemma required). Postgres + APScheduler are real (no in-memory fallback).
- Standalone sub-agent only: the orchestrator loop is NOT modified beyond registering the
  sub-agent in its config so its tool is discoverable.
- Latest stable pinned deps (apscheduler, sqlalchemy, psycopg[binary], pydantic v2).
