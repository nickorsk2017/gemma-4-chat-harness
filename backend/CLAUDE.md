# CLAUDE.md — Backend (FastAPI / Pydantic gateway + microservices)

Rules for the `backend/` subsystem. These are **in addition to**, never instead of, the
harness in [`.claude/CLAUDE.md`](../.claude/CLAUDE.md) and the root
[`CLAUDE.md`](../CLAUDE.md). All work still goes through the execution harness as a task.

**Precedence on conflict:** `.claude/` harness > root `CLAUDE.md` > this file.

## Folder Map
```
backend/
├── _common/                    # Shared across all microservices
│   ├── db/                     # DeclarativeBase + async session factory
│   ├── schemas/                # Shared Pydantic schemas (ApiResponse envelope)
│   └── env/                    # Environment variable definitions (pydantic-settings)
└── {name}/                     # One importable package per bounded context
    ├── routers/                # FastAPI route handlers (thin)
    ├── services/               # Business logic
    ├── models/                 # SQLAlchemy ORM models
    ├── schemas/                # Pydantic request/response schemas
    └── main.py                 # FastAPI app factory + Uvicorn entry
```
Each bounded context is a top-level importable package under `backend/` (e.g. `gateway/`),
so `gateway.main:app` resolves directly with no nested wrapper directory.

## Layers (respect boundaries)
- `routers/` — HTTP only. Validate input, call a service, return an `ApiResponse`
  envelope. No business logic, no MCP/DB calls inline.
- `services/` — business logic. The orchestrator MCP client and request mapping live
  here. Services accept and return Pydantic models, never raw dicts.
- `models/` — SQLAlchemy 2.x ORM models on the shared `_common.db.Base`.
- `schemas/` — Pydantic request/response contracts.
- `_common/` — shared envelope (`ApiResponse[T]`), settings, db primitives. No service
  may import another microservice; they share only `_common`.

## Rules
1. **Contracts first.** Define `schemas/` before routers. Cross-boundary data is always a
   Pydantic model.
2. **Thin routers.** Endpoints validate + delegate + envelope. Logic lives in `services/`.
3. **One envelope.** Every REST response is `ApiResponse[T]`:
   `{ status: "Success" | "Failed", data?: T, error_text?: string }`.
4. **Config, not constants.** URLs, modes, timeouts, origins, DB URL come from
   `_common/env` (env-backed). No hardcoded secrets.
5. **Structured errors, honest status codes.** No exception crosses the HTTP boundary
   unstructured — every error is an `ApiResponse.fail(...)` body, but with a truthful
   HTTP status: 400 (client/validation: empty prompt, bad attachment), 502
   (orchestration/upstream failure), 500 (unexpected). Success is 200.
6. **Always real.** The orchestrator MCP client sits behind an interface selected by
   config — there is NO mock mode. Default `GATEWAY_ORCHESTRATOR_MODE=stdio` spawns the
   real `master_orchestrator` MCP server as a subprocess; `http` connects to a running
   one over HTTP (the composed stack uses this). Spawn command/args are config (rule 4),
   never hardcoded. Tests stub the `OrchestratorClient` Protocol directly.
7. **MCP boundary.** The gateway is an MCP *client* of `master_orchestrator`; it calls the
   `orchestrate` tool and maps the returned envelope. It never imports `mcp/` packages.

## Stack conventions
- Python ≥ 3.11, async-first, fully type-hinted.
- FastAPI (latest), Pydantic v2, pydantic-settings, SQLAlchemy 2.x, fastmcp (MCP client),
  uvicorn — pinned in `pyproject.toml`.

## Running
```
cd backend
pip install -e .[dev]
# Real path (default): spawns master_orchestrator over stdio — it must be importable
# in this env (pip install -e ../mcp/master_orchestrator).
uvicorn gateway.main:app
# POST http://localhost:8000/api/chat        {"prompt":"hello"}
# POST http://localhost:8000/api/chat/files  multipart: prompt=... files=[img.png, doc.pdf]
```
