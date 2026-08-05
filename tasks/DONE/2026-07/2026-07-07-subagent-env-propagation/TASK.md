# TASK — 2026-07-07-subagent-env-propagation
owner: Engineer
immutable: true

## Requirements
- R1: stdio sub-agents spawned by the orchestrator must inherit the orchestrator
  process's full environment (`os.environ`), so secrets set on the mcp container
  (TAVILY_API_KEY, GEMMA_API_KEY, LANGSMITH_*, ORCHESTRATOR_*) reach each
  sub-agent subprocess. Today no `env` is passed, so the MCP stdio client only
  forwards a safe subset (PATH/HOME/…) and drops these keys — web_agent reports
  "TAVILY_API_KEY is not set" even when the container has it.
- R2: Fix at spawn/config time in `SubagentToolset.load()`: inject
  `env = {**os.environ, **spec_env}` into every stdio sub-agent connection
  (spec-provided env wins over inherited). Do not mutate the shared
  `settings.subagents`; build a fresh config dict.
- R3: Only stdio transports get `env` injected (http/sse specs untouched).

## Acceptance
- A1: After load, each stdio sub-agent's connection config carries an `env` dict
  containing the parent os.environ (TAVILY_API_KEY/GEMMA_API_KEY present when set
  on the parent).
- A2: `settings.subagents` is not mutated (no in-place edit of the global).
- A3: subagents.py py_compiles clean; no new dependencies.

## Constraints
- Touch only master_orchestrator/services/subagents.py.
