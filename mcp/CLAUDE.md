# MCP Agents — Project Rules

Multi-agent system built on **FastMCP**, **LangChain** (core + MCP adapters), and **Pydantic** (all latest versions).
Each agent is an independent MCP server. A `master_orchestrator` runs a **Gemma tool-calling
loop** over the sub-agents' tools, calling them **in parallel** when independent, then merges
their results into one answer.

## Folder structure

Every agent is its **own installable distribution** in a single top-level folder under
`mcp/`. The folder name **is** the import root (underscored, because Python identifiers
can't contain hyphens); the agent's code and its `pyproject.toml` live directly inside it —
there is no `packages/` wrapper and no `<dist-name>/<import_root>` doubling. Agents share
only `agent_core` (response envelope + LLM factory); no agent may import another agent.

```
mcp/
├── agent_core/                 # shared dist == import root
│   ├── {__init__,envelope,llm}.py
│   └── pyproject.toml
└── {name_agent}/               # one per agent (e.g. web_agent, doc_analyzer, ...)
    ├── db/                     # logic for db (persistence, caching, sessions)
    ├── schemas/
    │   ├── {model_name}.py     # Domain models (Pydantic)
    │   └── http.py             # HTTP request / response contracts
    ├── tools/
    │   └── {tool_name}.py      # MCP tools
    ├── prompts/
    │   └── {prompt_name}.py    # System / task prompts
    ├── config.py               # Settings (pydantic-settings)
    ├── main.py                 # MCP server entry point
    └── pyproject.toml          # distinct distribution: own name, deps, entry point
```

The repo-root `mcp/pyproject.toml` is a dev aggregator (editable-installs every package for
local work); it is NOT a shared umbrella package.

## Stack conventions

- **Language:** Python ≥ 3.11, fully type-hinted. Async-first.
- **MCP:** `fastmcp` (FastMCP v2). Each `main.py` builds a `FastMCP` instance and exposes tools.
- **LLM / tools:** `langchain-core` chat models. The orchestrator binds the sub-agents' tools to the model and runs a **tool-calling loop** (the model selects tools; the orchestrator executes them fail-soft and in parallel). Sub-agents are reached as MCP clients via `langchain-mcp-adapters`.
- **Multi-step logic:** implemented directly in async Python (no graph framework); keep it in `tools/` behind Pydantic contracts.
- **Validation:** `pydantic` v2 for all domain models and I/O contracts. Never pass around raw dicts across boundaries.
- **Settings:** `pydantic-settings` `BaseSettings` in every `config.py`, loaded from env / `.env`.

## Rules

1. **One responsibility per agent.** `web_agent` fetches from the internet, `doc_analyzer` reads PDFs,
   `image_analyzer` inspects images. The orchestrator never does domain work itself — it only routes and merges.
2. **Contracts first.** Define `schemas/*.py` before writing tools. Tools accept and return Pydantic models.
   `schemas/http.py` holds the request/response envelope every tool shares.
3. **Tools are thin.** A tool in `tools/` validates input, calls into a provider/service, returns a schema. No business logic buried in `main.py`.
4. **Prompts are data.** All prompt text lives in `prompts/`, never inlined in tools.
5. **Config, not constants.** URLs, model names, timeouts, API keys come from `config.py` (env-backed). No hardcoded secrets.
6. **Parallelism.** The orchestrator dispatches sub-agent calls concurrently (`asyncio.gather`) and only
   returns once every sub-task resolves. A slow/failed sub-agent must not block the others' results.
7. **Fail soft.** Every tool returns a structured response with a `status` field; errors are captured in the
   envelope, never raised across the MCP boundary.
8. **Mock by default.** Providers ship with mock implementations behind an interface so the system runs
   with zero external keys. Swap in real APIs via `config.py` without touching tool code.

## Agents

| Agent                | Role                                                                 |
|----------------------|---------------------------------------------------------------------|
| `master_orchestrator`| Receives the user prompt, runs a Gemma tool-calling loop over the sub-agent MCP servers (calling them in parallel when independent), merges results into one response, and keeps per-thread memory. |
| `web_agent`          | Retrieves live data from the internet (news, weather, general web).  |
| `doc_analyzer`       | Analyzes documents, primarily PDFs (extract, summarize, Q&A).        |
| `image_analyzer`     | Analyzes images (describe, detect, OCR).                             |

## Running

Each sub-agent runs as its own MCP server — via its console script (`web-agent`,
`doc-analyzer`, `image-analyzer`, `master-orchestrator`) or its module
(`python -m {name_agent}.main`). The orchestrator connects to them as MCP clients over
stdio/HTTP (config in `master_orchestrator/config.py`) and never imports a sub-agent's
package. See top-level `README.md` for install + run commands.
