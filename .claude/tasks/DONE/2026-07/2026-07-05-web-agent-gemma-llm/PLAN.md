# PLAN — 2026-07-05-web-agent-gemma-llm

## v1

### Design
D1. `web_agent/prompts/generate.py` — three format-string prompts:
    `NEWS_GEN(query, limit)`, `WEATHER_GEN(location)`, `PAGE_GEN(url)`. Each instructs the
    model to fill the corresponding schema. Honest framing: the model reports from its own
    knowledge (it cannot browse), so prompts say "best-effort, note uncertainty in text".
D2. `web_agent/tools/providers.py`:
    - `_llm_ready() -> bool`: `settings.llm_provider != "mock" and bool(settings.llm_api_key)`.
    - `_chat_model()` cached module-level via `agent_core.llm.build_chat_model(
      provider=settings.llm_provider, model=settings.llm_model,
      api_key=settings.llm_api_key, base_url=settings.llm_base_url)`.
    - Each provider: mock branch unchanged; real branch
      `await _chat_model().with_structured_output(Schema).ainvoke(PROMPT.format(...))`.
    - Replace old gates (`search_provider`/`weather_provider`) with `_llm_ready()`;
      keep those settings in config (used elsewhere/mock labels) — config.py untouched
      (llm block already added by task 2026-07-05-gemma-nvidia-llm).
D3. `web_agent/pyproject.toml`: no new deps (factory + ChatOpenAI come via agent-core;
    `with_structured_output` is langchain-core, transitive through agent-core).
D4. Hygiene: append `.env` (+ `.env.*` except `.env.example`) to `.gitignore`; add
    `NVIDIA_API_KEY=` line + comment to `.env.example`. Local `.env` gets the real token
    (untracked; environment provisioning, recorded in EXEC).

### Files touched
web_agent/tools/providers.py, web_agent/prompts/generate.py (new), .gitignore, .env.example
(+ local untracked .env)

### Validation strategy
- py_compile changed .py files; AST/source asserts (llm gate, structured output, prompts).
- Stubbed runtime test: stub langchain/pydantic-free path is impractical for providers
  (pydantic schemas involved); instead stub `agent_core.llm.build_chat_model` and
  `web_agent.config.settings` via sys.modules to drive both branches of `fetch_news`.
- `git check-ignore .env`; grep tracked files for `nvapi-`.

## v2 (requirement update: single env var renamed to GEMMA_API_KEY)
D5. Rename `validation_alias="NVIDIA_API_KEY"` -> `"GEMMA_API_KEY"` in all four configs
    (master_orchestrator, doc_analyzer, web_agent, image_analyzer). `.env.example` and local
    `.env` use `GEMMA_API_KEY`. Everything else from v1 unchanged.
