# TASK — 2026-07-05-web-agent-gemma-llm
owner: Engineer
immutable: true

## Requirements
- R1: web_agent must obtain ALL its tool results (news, weather, page fetch) through the
  gemma LLM: `google/gemma-4-31b-it` via the NVIDIA OpenAI-compatible endpoint, using the
  shared factory `agent_core.llm.build_chat_model` and web_agent's existing `llm_*` settings.
- R2: Real path gates on `settings.llm_provider != "mock" and settings.llm_api_key`;
  without GEMMA_API_KEY the current mock responses remain byte-identical.
- R3: LLM output is parsed into the existing Pydantic schemas (NewsResult, Weather, WebPage)
  via structured output; tools/web_tools.py stays thin and unchanged.
- R4: Prompts live in `web_agent/prompts/` per mcp/CLAUDE.md conventions.
- R5: No hardcoded API keys anywhere. Key comes only from env `GEMMA_API_KEY`.
  Repo hygiene: add `.env` to `.gitignore`; document `GEMMA_API_KEY` in `.env.example`.
  (Provision the user's actual token into local untracked `.env` — environment step, not code.)

## Acceptance
- A1: With GEMMA_API_KEY set, each provider builds the gemma model (nvidia provider,
  NVIDIA base_url) and returns schema-typed results from LLM structured output (no live
  network call needed to verify wiring).
- A2: With key unset, all three providers return today's mock objects; files compile.
- A3: `git check-ignore .env` passes; no `nvapi-` string anywhere in tracked files.

## Constraints
- Changes limited to web_agent/, .gitignore, .env.example (and local .env), plus renaming the
  key alias NVIDIA_API_KEY -> GEMMA_API_KEY in all four agent config.py files.
- No real network calls during validation.
