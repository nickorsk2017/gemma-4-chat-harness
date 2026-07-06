# EXEC — 2026-07-05-remove-mock-llm

## v1 (implements PLAN v1; 10 files)
- agent_core/llm.py: FakeListChatModel + mock branch + mock_responses removed; added
  LLMConfigError; provider="mock" and missing api_key now raise it; defaults
  provider=nvidia, model=DEFAULT_NVIDIA_MODEL; unknown provider -> LLMConfigError (D1).
- master_orchestrator/tools/planner.py: _MOCK_PLAN, mock branch, PydanticOutputParser and
  AgentName imports removed; always real structured-output chain (D2).
- master_orchestrator/tools/graph.py: synthesis chain unconditional real model (D3).
- web_agent/tools/providers.py: _llm_ready + mock branches + NewsItem import removed (D4).
- doc_analyzer/tools/providers.py: summarize_document/ask_document implemented — extract
  (mock extraction path kept) -> SUMMARIZE_DOC/ANSWER_DOC prompt + document text ->
  cached gemma model with_structured_output(DocSummary|DocAnswer); mock-LLM branches and
  NotImplementedError for LLM paths removed. pyproject: + langchain-core (D5).
- Config comments (4 agents) + .env.example: GEMMA_API_KEY REQUIRED, no mock LLM fallback;
  dropped ORCHESTRATOR_LLM_PROVIDER=mock suggestion (D6).
