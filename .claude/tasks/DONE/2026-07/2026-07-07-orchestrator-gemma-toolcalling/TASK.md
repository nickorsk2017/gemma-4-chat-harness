# TASK — 2026-07-07-orchestrator-gemma-toolcalling
owner: Engineer
immutable: true

## Requirements
- R1: The master_orchestrator MUST orchestrate sub-agents via a Gemma (Novita
  OpenAI-compatible) tool-calling loop: the model is bound the sub-agents' tools
  and itself decides which to call; the orchestrator executes the calls and feeds
  results back until the model produces a final answer.
- R2: Remove all LangGraph logic (StateGraph, nodes/edges, checkpointer,
  @traceable/LangSmith tracing wiring) from master_orchestrator.
- R3: Remove the separate Planner (structured-output plan chain, Plan schema,
  planner prompts) and other now-dead "junk".
- R4: Preserve multi-turn thread memory (conversation history + gateway-extracted
  document text stored by name) WITHOUT LangGraph, and keep delete_thread
  working. In-memory backend by default; optional Postgres via
  ORCHESTRATOR_DATABASE_URL.
- R5: Preserve fail-soft dispatch (rule 7) and parallel sub-agent execution
  (rule 6): when the model requests several tools in one turn they run
  concurrently and a failing sub-agent never sinks the run.
- R6: doc_analyzer tool calls must have the stored document text injected at
  dispatch time; the model never carries raw document text.

## Acceptance
- A1: orchestrate and delete_thread MCP tools keep their existing request /
  AgentResponse[OrchestrationResult] contracts (gateway unchanged).
- A2: No import of langgraph, langsmith, or master_orchestrator.tools.planner /
  .tools.graph / .db.checkpointer remains in the package.
- A3: master_orchestrator pyproject.toml no longer depends on langgraph,
  langgraph-checkpoint-postgres, or langsmith.
- A4: Memory tests pass: document text + history persist across turns in a thread,
  threads are isolated, doc tool calls receive injected stored text, and
  delete_thread clears a thread.
- A5: Every module in the package byte-compiles.

## Constraints
- Obey mcp/CLAUDE.md rules (contracts-first schemas, thin tools, prompts-as-data,
  config-not-constants, fail-soft envelopes, parallel dispatch) and the shared
  AgentResponse envelope.
- Sub-agent set is discovered from config; do not hardcode a stale tool list.
- Scope is mcp/master_orchestrator (+ its docs); do not modify sub-agents.
