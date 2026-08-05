# EXEC — orchestrator-http-robust

## v1
- main.py `_disable_sdk_rebinding_protection`: wrapped SDK import + patch in
  try/except; on failure prints a skip notice and continues (Host-normalizer
  middleware still enforces localhost Host). Prevents a version-drift ImportError/
  AttributeError from crash-looping the container (which surfaces to the gateway
  as "Client failed to connect: All connection attempts failed").
- main.py `_run_http`: print bound address ("serving streamable-HTTP on
  http://0.0.0.0:8100/mcp") before uvicorn.run for operator verification.
- Scope: main.py only. byte-compile + compileall PASS.
