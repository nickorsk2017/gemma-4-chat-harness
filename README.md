# agent-chat

AI-agent chat system: a web chat where one **master orchestrator** splits each user
prompt into sub-tasks and dispatches them to specialized **MCP sub-agents in
parallel** — live web search/news, PDF/document analysis, and image analysis — then
synthesizes a single answer. Conversation history and uploaded-document text persist
per thread in PostgreSQL.

All agents share **one** LLM: `google/gemma-4-31b-it` served by Novita's
OpenAI-compatible endpoint (configurable via `GEMMA_MODEL`). Live search is real
internet data via Tavily's hosted MCP server.

## Architecture

```
Browser ── Next.js frontend (:3000)
              │  REST
              ▼
         FastAPI gateway (:8000)  ── uploads volume, 502-maps upstream failures
              │  streamable-HTTP MCP
              ▼
         master_orchestrator (:8100 in-docker "mcp" service)
              │  Gemma tool-calling loop → parallel tool calls over stdio
              ├─ web_agent      — search_web (Tavily MCP)
              ├─ doc_analyzer   — summarize_document / ask_document (PDF text from thread)
              └─ image_analyzer — describe / detect_objects / ocr
              │
         PostgreSQL — orchestrator thread store (history + stored document text)
```

## Repository structure

| Path | What lives here |
|---|---|
| `frontend/` | Next.js + Tailwind 4 + Zustand chat UI ([rules](frontend/CLAUDE.md)) |
| `backend/` | FastAPI gateway + services ([rules](backend/CLAUDE.md)) |
| `mcp/` | Orchestrator + sub-agents, FastMCP ([rules](mcp/CLAUDE.md)) |
| `mcp/agent_core/` | Shared response envelope + the single LLM factory (`llm.py`) |
| `mcp/master_orchestrator/` | Gemma tool-calling loop over sub-agents + thread memory store |
| `mcp/web_agent/`, `mcp/doc_analyzer/`, `mcp/image_analyzer/` | Sub-agents (independent distributions) |
| `mcp/scripts/gemma_healthcheck.py` | Docker-free LLM reachability probe |
| `.claude/` | Execution harness: runner, roles, hooks, task artifacts |
| `docker-compose.yml`, `Makefile` | The whole stack + dev commands |

## Quick start

```bash
cp .env.example .env      # then fill the two keys below
make up                   # build + start postgres, mcp, backend, frontend
open http://localhost:3000
```

Required in `.env`:

- `GEMMA_API_KEY` — Novita API key; the single LLM key for every agent (no mock fallback).
- `TAVILY_API_KEY` — Tavily key for web_agent's live `search_web` / `get_news`.

Optional: `LANGSMITH_*` (tracing), port overrides (`FRONTEND_PORT`, `BACKEND_PORT`,
`MCP_PORT`), timeout budgets (`LLM_REQUEST_TIMEOUT_S`, `GATEWAY_ORCHESTRATOR_TIMEOUT_S`).
See [.env.example](.env.example) for the full annotated list.

### Make targets

```
make up / up-fg / down / restart      start & stop the stack
make build / rebuild                  build images (rebuild = no cache)
make logs / ps                        observe
make clean                            stop + remove volumes and local images
make gemma-check                      probe the LLM endpoint (no docker needed)
make mcp-check                        liveness-check the mcp service API (no agents/LLM invoked)
```

**After changing any code or dependency under `mcp/`, `backend/`, or `frontend/`,
run `make rebuild`** — images bake the code at build time; `make up` alone reuses
stale images.

### Health check

`make gemma-check` bootstraps a local `.venv-gemma`, reads `GEMMA_API_KEY` from
`.env`, and sends one real chat completion to Novita (4 attempts with backoff).
Exit 0 with a model reply = the LLM path is healthy.

## The execution harness (`.claude/`)

All development in this repo — code, config, docs — flows through a deterministic,
artifact-driven harness; chat/LLM context is never a source of truth. Full spec:
[`.claude/CLAUDE.md`](.claude/CLAUDE.md); binding summary in the root
[`CLAUDE.md`](CLAUDE.md).

- **Tasks, not conversations.** Every change is a task under `tasks/CURRENT/`
  (archived to `tasks/DONE/<YYYY-MM>/` on closure) with five artifacts:
  `TASK.md` (requirements), `PLAN.md`, `EXEC.md`, `VALIDATION.md`, and
  `STATE.yaml` — the only routing source.
- **Roles.** Engineer (human: writes TASK.md, approves) → Planner (all design
  reasoning → PLAN.md) → Executor (implementation → EXEC.md) → Validator
  (quality gate → VALIDATION.md). LOW-complexity tasks skip the Planner;
  HIGH-complexity tasks add an Engineer approval step.
- **Runner.** `.claude/runner.py` is the deterministic dispatcher:
  `new <id>` / `use` / `status` / `next` / `done`. A task is finished only when
  `STATE.yaml` reads `stage: DONE, status: PASS`; `runner.py done` archives it.
- **Enforcement.** A PreToolUse hook enforces the per-role read/write matrix and
  legal stage transitions; a pre-commit hook plus
  `.github/workflows/harness-gate.yml` (`ci_check.py`) block commits/pushes with
  escalated tasks or open issues. Validation failures route back by issue type
  (requirement → Engineer, architecture → Planner, logic → Executor) with a
  2-iteration escalation cap.

## Ports

| Service | Host | Notes |
|---|---|---|
| frontend | 3000 | chat UI |
| backend | 8000 | REST gateway (`/api/chat`, `/api/chat/files`) |
| mcp | 8100 | orchestrator, streamable-HTTP `/mcp` |
| postgres | — | internal only (compose network) |
