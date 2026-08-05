# EXEC — 2026-07-07-subagent-env-propagation

## v1
master_orchestrator/services/subagents.py:
- Added `import os`.
- load() now builds the client from `cls._server_specs()` instead of the raw
  `settings.subagents`.
- New `_server_specs()` staticmethod: copies each spec (`dict(spec)`), and for
  stdio transports sets `env = {**os.environ, **(spec env or {})}` so the parent
  container env (TAVILY_API_KEY/GEMMA_API_KEY/LANGSMITH_*/…) reaches every
  sub-agent subprocess; http/sse specs pass through with no env. Shared
  settings.subagents is never mutated (fresh dict + per-spec copy).
py_compile OK.
