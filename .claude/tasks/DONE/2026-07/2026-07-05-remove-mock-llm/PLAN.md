# PLAN — 2026-07-05-remove-mock-llm

## v1

### Design
D1. agent_core/llm.py: drop FakeListChatModel import, mock branch, `mock_responses` param.
    New: `class LLMConfigError(RuntimeError)`. Defaults become provider="nvidia",
    model=DEFAULT_NVIDIA_MODEL. Guards: `provider == "mock"` -> LLMConfigError("mock LLM
    removed; configure GEMMA_API_KEY"); `not api_key` -> LLMConfigError("GEMMA_API_KEY is
    not set ..."). nvidia/openai/anthropic branches unchanged.
D2. master_orchestrator/tools/planner.py: delete _MOCK_PLAN + mock branch +
    PydanticOutputParser and AgentName imports; chain = prompt |
    real_model.with_structured_output(Plan); docstring updated.
D3. master_orchestrator/tools/graph.py: build_synthesis_chain loses the conditional —
    always real model.
D4. web_agent/tools/providers.py: delete `_llm_ready` and all mock branches (NewsItem
    import too); every provider: cached model -> with_structured_output(Schema).ainvoke.
D5. doc_analyzer/tools/providers.py: keep extract_text as-is. summarize_document /
    ask_document: `text = (await extract_text(path, None)).text`; prompt =
    SUMMARIZE_DOC/ANSWER_DOC.format(...) + "\n\nDocument text:\n" + text; cached model via
    factory -> with_structured_output(DocSummary|DocAnswer).ainvoke. Remove mock-LLM
    branches and NotImplementedError. pyproject: + langchain-core>=0.3.0.
D6. Config comments (4 agents): "GEMMA_API_KEY required; no mock LLM fallback".
    .env.example: same wording; drop ORCHESTRATOR_LLM_PROVIDER=mock suggestion.

### Files touched (10)
agent_core/llm.py; master_orchestrator/tools/{planner,graph}.py;
web_agent/tools/providers.py; doc_analyzer/tools/providers.py; doc_analyzer/pyproject.toml;
{master_orchestrator,doc_analyzer,web_agent,image_analyzer}/config.py (comments);
.env.example

### Validation strategy
py_compile all; source asserts for A2; stub runtime: factory errors (no key / mock),
web_agent + doc_analyzer providers full path with stubbed factory/config/schemas.
