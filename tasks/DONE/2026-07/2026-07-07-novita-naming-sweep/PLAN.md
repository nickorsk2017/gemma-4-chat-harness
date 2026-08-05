# PLAN — 2026-07-07-novita-naming-sweep

## v1
Alias removal is safe: grep shows NVIDIA_BASE_URL/DEFAULT_NVIDIA_MODEL imported
only by master_orchestrator/image_analyzer/doc_analyzer/web_agent config.py.
Mechanical sweep:
1. agent_core/llm.py — delete the two alias lines + their comment.
2. 4x config.py — import { DEFAULT_MODEL, NOVITA_BASE_URL } from agent_core.llm;
   llm_provider "nvidia" -> "novita"; llm_model = DEFAULT_MODEL;
   llm_base_url = NOVITA_BASE_URL; comment "via the NVIDIA OpenAI-compatible
   endpoint" -> "via Novita's OpenAI-compatible endpoint"; drop stale ":free".
3. doc_analyzer & image_analyzer providers.py docstrings, web_agent
   prompts/generate.py docstring — "google/gemma-4-31b-it via Novita".
4. .env.example header for the LLM section -> Novita.
llm_provider values are display-only (build_chat_model ignores provider) — R3 safe.
