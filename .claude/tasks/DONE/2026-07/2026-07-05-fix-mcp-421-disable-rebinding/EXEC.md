# EXEC — 2026-07-05-fix-mcp-421-disable-rebinding

## v1

### Change
`mcp/master_orchestrator/main.py` (single file, R3):
- `_disable_sdk_rebinding_protection()` — pins `TransportSecurityMiddleware.__init__`
  so every instance is constructed with
  `TransportSecuritySettings(enable_dns_rebinding_protection=False)`, regardless of
  what fastmcp passes internally. Called at the top of `_run_http()` only; stdio
  path untouched. Security rationale in the docstring (R2/constraint).
- Host-normalizing middleware kept as defense-in-depth.

### Verification (sandbox)
- `py_compile` clean.
- Simulation using the SDK's verbatim validation semantics (fetched from
  python-sdk main): with fastmcp-style construction under ANY settings
  (None / strict allowlist / empty allowlist), no Host value can produce 421
  after the patch. Repro case (`mcp:8100`, `localhost:8100` vs allowlist
  `127.0.0.1:8000`) fails before the patch, passes after.
- A1 runtime: host-side `docker compose up -d --build mcp`.
