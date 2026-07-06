# TASK — 2026-07-05-langgraph-thread-memory
owner: Engineer
immutable: true

## Problem
Chat is stateless: each /api/chat call runs the orchestrator graph fresh. A follow-up
question ("а какие технологии в моем CV?") after a PDF upload fails because neither the
conversation history nor the parsed document text survives between requests.

## Requirements
- R1: Persist conversation history with LangGraph memory (checkpointer) backed by
  PostgreSQL, keyed by `thread_id`, using the official LangGraph/LangChain API
  (`langgraph-checkpoint-postgres`, `AsyncPostgresSaver`, `add_messages`).
- R2: When a PDF is parsed (pypdf), the extracted text MUST be stored in the same
  thread state so later turns can use it without re-uploading the file.
- R3: A follow-up question in the same thread (no new attachment) must be answered
  from the stored history + stored document text.
- R4: `thread_id` travels end-to-end: frontend (kept per chat session in the Zustand
  store) -> gateway ChatRequest / multipart form -> orchestrator OrchestrateRequest
  -> graph configurable.thread_id. Gateway generates one if absent and returns it
  in the reply so the client can adopt it.
- R5: PostgreSQL runs as a service in docker-compose; connection URL comes from
  env-backed settings (no hardcoded constants). Graceful dev fallback when no
  database URL is set (in-memory checkpointer) so stdio/local mode still works.
- R6: No regressions: existing endpoints keep their envelope contracts; new fields
  are optional / backward-compatible.

## Acceptance
- A1: Turn 1: prompt + CV.pdf -> answer; thread checkpoint contains the messages and
  the extracted PDF text.
- A2: Turn 2: same thread_id, prompt "какие технологии в моем CV?" without a file ->
  correct answer from stored text; no "данные не были переданы" failure.
- A3: Fresh thread_id -> no leakage of another thread's history.
- A4: Existing tests pass; stack boots via docker compose with the new postgres service.

## Constraints
- Follow subsystem CLAUDE.md rules (contracts first, tools thin, prompts are data,
  config not constants, fail soft, parallel dispatch preserved).
- Out of scope: thread-list UI, RAG/vector storage, auth/per-user isolation.
