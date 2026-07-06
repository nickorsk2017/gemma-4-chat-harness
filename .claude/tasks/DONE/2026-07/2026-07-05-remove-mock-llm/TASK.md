# TASK — 2026-07-05-remove-mock-llm
owner: Engineer
immutable: true

## Requirements
- R1: Remove the mock LLM everywhere: `FakeListChatModel` and the `mock` provider are
  deleted from `agent_core/llm.py`; every LLM call is a real gemma call
  (google/gemma-4-31b-it @ NVIDIA endpoint) via the shared factory.
- R2: Missing `GEMMA_API_KEY` (or provider "mock") -> explicit configuration error at model
  build time; no silent fallback.
- R3: Remove mock-LLM branches from master_orchestrator (planner.py, graph.py) and
  web_agent providers; chains always use the real model.
- R4: doc_analyzer: implement `summarize_document` and `ask_document` for real through
  gemma structured output over the extracted text (`extract_text` provider stays as-is,
  incl. its mock extraction path). Delete their mock-LLM branches and NotImplementedError.
- R5: Non-LLM mocks (web search labels, image vision, PDF extraction, gateway mode) are out
  of scope. Update comments/.env.example so nothing claims an LLM mock fallback exists.

## Acceptance
- A1: `build_chat_model` raises a clear error with no/empty api_key and for provider "mock";
  with key returns ChatOpenAI @ NVIDIA base_url.
- A2: No `FakeListChatModel`, `mock_responses`, `_MOCK_PLAN`, or `_llm_ready` mock-gates
  remain in mcp/ LLM paths (source check).
- A3: doc_analyzer summarize/ask runtime path (stubbed model): extract -> prompt with doc
  text -> structured DocSummary/DocAnswer; no NotImplementedError.
- A4: All changed files compile; no hardcoded keys.

## Constraints
- No live network calls in validation.
- Approval: HIGH task; Engineer (user) explicitly ordered mock removal and confirmed the
  "everywhere + doc_analyzer" scope in chat — recorded as approval for PLAN v1.
