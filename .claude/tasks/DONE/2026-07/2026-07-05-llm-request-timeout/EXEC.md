# EXEC — 2026-07-05-llm-request-timeout
## v1
agent_core/llm.py: DEFAULT_REQUEST_TIMEOUT_S=90, env override LLM_REQUEST_TIMEOUT_S;
nvidia/openai branches pass timeout + max_retries=1. 1 file.
