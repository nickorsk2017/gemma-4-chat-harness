# VALIDATION — 2026-07-07-subagent-env-propagation

## v1 — PASS
- A1 PASS: stubbed _server_specs() test — stdio 'web_agent' gets an `env` dict
  containing forwarded TAVILY_API_KEY (sentinel) and GEMMA_API_KEY (parent).
- A2 PASS: settings.subagents not mutated (no `env` key leaks back into the
  global spec after the call).
- A3 PASS: subagents.py py_compiles clean; no new deps (stdlib os only).
- Extra: http/sse spec left untouched (no `env`); spec-provided env wins over
  the inherited parent value. All 6 assertions PASS (exit 0).
- Live confirmation left to Engineer: `make up` then "Последние новости" should
  now return real Tavily results (web_agent subprocess sees TAVILY_API_KEY).
