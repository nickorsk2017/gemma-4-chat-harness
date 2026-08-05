# PLAN — 2026-07-07-subagent-env-propagation

## v1

### Root cause
Orchestrator spawns sub-agents via `MultiServerMCPClient(settings.subagents)`.
Each spec is `{command, args, transport:"stdio"}` with NO `env`. The MCP stdio
client, when env is None, forwards only `get_default_environment()` (PATH, HOME,
USER, SHELL, TERM, LOGNAME) — arbitrary secrets are stripped. So the web_agent
subprocess starts without TAVILY_API_KEY (and GEMMA_API_KEY), and its pydantic
`WebAgentSettings()` resolves them to None -> "TAVILY_API_KEY is not set". The
orchestrator itself works because it runs in the container's main process, which
DOES have the compose-provided env.

### Fix (subagents.py only)
Before constructing the client, build a fresh server map that injects the parent
environment into each stdio spec:

    import os
    ...
    servers: dict[str, dict[str, object]] = {}
    for name, spec in settings.subagents.items():
        cfg = dict(spec)  # copy — never mutate the shared settings.subagents
        if cfg.get("transport", "stdio") == "stdio":
            cfg["env"] = {**os.environ, **(cfg.get("env") or {})}
        servers[name] = cfg
    client = MultiServerMCPClient(servers)

- Full `os.environ` is forwarded (per the compose comment: sub-agents inherit
  this env), so TAVILY/GEMMA/LANGSMITH/ORCHESTRATOR_* all propagate.
- Spec-provided `env` wins over inherited (right-hand merge), preserving any
  explicit override.
- Only stdio specs get `env` (http/sse have no subprocess) — R3.
- `dict(spec)` copy + fresh `servers` dict -> `settings.subagents` untouched (A2).

### Security note
Passing the full environment to first-party trusted sub-agents is the intended
design (they need the same secrets). No third-party processes are spawned, so
broad propagation is acceptable here; narrowing to an allowlist is a possible
future hardening but out of scope.

### Validation
py_compile subagents.py. Full env-map assertion needs langchain_mcp_adapters
(absent in sandbox) -> Validator does a stubbed unit check of the map-building
logic (stdio gets env incl. a sentinel var; http untouched; settings.subagents
unmutated). Live confirmation (`make up` + news prompt returns real results)
left to Engineer.
