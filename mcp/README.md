# mcp-agents

A multi-agent MCP system. A **master orchestrator** receives a user prompt and,
via a **Gemma tool-calling loop**, calls specialized sub-agents (in **parallel**
when independent) and merges the results into a single answer.

Built on **FastMCP**, **LangChain** (core + MCP adapters), and **Pydantic** (latest).

## Agents

| Agent                 | Role |
|-----------------------|------|
| `master_orchestrator` | Gemma tool-calling loop: calls sub-agents (concurrently when independent) as MCP clients, merges results; keeps thread memory. |
| `web_agent`           | Live internet data — news, weather, page fetch. |
| `doc_analyzer`        | Document analysis — PDF extract, summarize, Q&A. |
| `image_analyzer`      | Image analysis — describe, detect, OCR. |

Each agent is an **independent, separately-installable Python distribution** in its own
top-level folder under `mcp/` (the folder name is the import root), following the layout
documented in [`CLAUDE.md`](./CLAUDE.md). They share only `agent_core` (the response
envelope + LLM factory) — no agent imports another agent.

| Distribution         | Import root / folder  | Path        |
|----------------------|-----------------------|-------------|
| `agent-core`         | `agent_core`          | `mcp/agent_core`          |
| `web-agent`          | `web_agent`           | `mcp/web_agent`           |
| `doc-analyzer`       | `doc_analyzer`        | `mcp/doc_analyzer`        |
| `image-analyzer`     | `image_analyzer`      | `mcp/image_analyzer`      |
| `master-orchestrator`| `master_orchestrator` | `mcp/master_orchestrator` |

## How it works

```
user prompt
     │
     ▼
master_orchestrator ── Gemma tool-calling loop (bind sub-agent tools)
     │        model picks tools ─▶ run them ─▶ tool results ─▶ model ─▶ answer
     │  (MCP client calls, asyncio.gather for parallel tool calls)
     ├───────────────┬─────────────────────┐
     ▼               ▼                      ▼
 web_agent      doc_analyzer          image_analyzer   ← each an MCP server
```

The model is bound the sub-agents' tools and decides which to call; independent
tool calls in one turn run together with `asyncio.gather`. A slow or failing
sub-agent is captured as an error result (fail-soft envelope) and does not block
the others. Conversation history and gateway-extracted document text persist per
thread in the orchestrator's own store (in-memory, or Postgres when
`ORCHESTRATOR_DATABASE_URL` is set).

## Install

Each agent is its own distribution, so install only what you deploy. `agent-core` is a
dependency of every agent — install it first (or let your resolver pull it from the path).

Install a single agent standalone:

```bash
pip install -e agent_core
pip install -e web_agent          # or doc_analyzer / image_analyzer / master_orchestrator
```

Install the whole fleet for local development (order matters — `agent_core` first):

```bash
pip install -e agent_core
pip install -e web_agent -e doc_analyzer \
            -e image_analyzer -e master_orchestrator
```

The root `pyproject.toml` is a **dev aggregator only** — it editable-installs each agent
in its `mcp/<name>` folder; it does not build a shared umbrella package.

## Run

Each sub-agent is its own MCP server. Run via its console script or its module:

```bash
web-agent           # or: python -m web_agent.main
doc-analyzer        # or: python -m doc_analyzer.main
image-analyzer      # or: python -m image_analyzer.main
```

Run the orchestrator (it spawns / connects to the sub-agents as MCP servers per its config):

```bash
master-orchestrator # or: python -m master_orchestrator.main
```

Then call the `orchestrate` tool with `{ "request": { "prompt": "...", "context": { ... } } }`.
Example contexts: `{"location": "Berlin"}`, `{"document_name": "report.pdf",
"document_text": "<extracted text>"}` (PDF text is extracted by the gateway —
doc_analyzer never reads files), `{"image_path": "/tmp/photo.jpg"}`.

## Mocks vs. real providers

Everything ships with **mock providers**, so the whole system runs with **no API
keys**. To go live, set the relevant env vars (see `config.py` in each agent) —
tool code doesn't change:

- `WEB_AGENT_SEARCH_PROVIDER`, `WEB_AGENT_SEARCH_API_KEY`, `WEB_AGENT_WEATHER_*`
- `DOC_ANALYZER_*`, `IMAGE_ANALYZER_*`
- `GEMMA_API_KEY` (the orchestration model; required — no mock fallback)

## Conventions

See [`CLAUDE.md`](./CLAUDE.md) for the required folder structure and the rules
every agent follows (contracts-first schemas, thin tools, prompts-as-data,
env-backed config, fail-soft envelopes, parallel dispatch).
