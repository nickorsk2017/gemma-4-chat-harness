# PLAN — 2026-07-05-gemma-nvidia-llm

## v1

### Design
Single point of connection: the shared factory `mcp/agent_core/llm.py`. Agents keep
per-agent settings but all default to the same NVIDIA/gemma target; the API key is a
single cross-agent env var `NVIDIA_API_KEY`.

D1. `agent_core/llm.py`
   - Module constants: `NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"`,
     `DEFAULT_NVIDIA_MODEL = "google/gemma-4-31b-it"`.
   - `build_chat_model(..., base_url: str | None = None)` new keyword.
   - New branch `provider == "nvidia"`: lazy-import `langchain_openai.ChatOpenAI`,
     return `ChatOpenAI(model=model, api_key=api_key, temperature=temperature,
     base_url=base_url or NVIDIA_BASE_URL)`.
   - `provider == "openai"` branch also passes `base_url` through (None => default OpenAI).
   - Mock fallback unchanged: `provider == "mock" or not api_key` -> FakeListChatModel.

D2. `agent_core/pyproject.toml`: add `langchain-openai>=0.3.0` to dependencies (all agents
   now target the NVIDIA endpoint; keeping it optional would make the default path crash).

D3. Config blocks — identical shape in all four agents, using each agent's existing
   `env_prefix` for provider/model/base_url and a shared alias for the key:
   ```python
   llm_provider: str = "nvidia"                       # "mock" disables
   llm_model: str = DEFAULT_NVIDIA_MODEL
   llm_base_url: str = NVIDIA_BASE_URL
   llm_api_key: str | None = Field(default=None, validation_alias="NVIDIA_API_KEY")
   ```
   - `master_orchestrator/config.py`: replace mock defaults, add `llm_base_url`, alias key.
   - `doc_analyzer/config.py`: same (adds `llm_model`, `llm_base_url`).
   - `web_agent/config.py`, `image_analyzer/config.py`: add the block (new).
   - Import constants from `agent_core.llm` to avoid duplicated literals.

D4. Call sites `master_orchestrator/tools/planner.py` and `tools/graph.py`: pass
   `base_url=settings.llm_base_url` in the real-provider branch. Mock guard
   (`provider == "mock" or not llm_api_key`) untouched -> R5 holds.

D5. No changes to doc_analyzer/image_analyzer providers.py (real chains remain
   NotImplementedError per TASK constraint); their configs are ready for wiring later.

### Files touched (8)
mcp/agent_core/llm.py, mcp/agent_core/pyproject.toml,
mcp/master_orchestrator/config.py, mcp/master_orchestrator/tools/planner.py,
mcp/master_orchestrator/tools/graph.py, mcp/doc_analyzer/config.py,
mcp/web_agent/config.py, mcp/image_analyzer/config.py

### Validation strategy (for Validator)
- Import check of all configs with env clean (no NVIDIA_API_KEY) -> settings load, mock path.
- Unit check: `build_chat_model(provider="nvidia", model=..., api_key="x")` returns ChatOpenAI
  with `openai_api_base == NVIDIA_BASE_URL` (no network).
- With env `NVIDIA_API_KEY=x`: orchestrator settings resolve `llm_api_key == "x"`.
