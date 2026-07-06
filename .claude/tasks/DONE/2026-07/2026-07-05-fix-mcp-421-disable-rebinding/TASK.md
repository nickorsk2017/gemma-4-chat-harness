# TASK — 2026-07-05-fix-mcp-421-disable-rebinding
owner: Engineer
immutable: true

## Requirements
- R1: Follow-up to 2026-07-05-fix-mcp-421-host-validation: host run showed the new
  uvicorn path live but POST /mcp still 421. SDK source confirms: with protection
  enabled, `allowed_hosts` defaults to EMPTY (no implicit localhost), and fastmcp
  builds the allowlist internally without a stable way to see/extend it. Rewriting
  Host is therefore guess-based; instead, deterministically disable the SDK's
  DNS-rebinding protection for this deployment.
- R2: Use the SDK's own public settings type (`TransportSecuritySettings
  (enable_dns_rebinding_protection=False)`) applied to `TransportSecurityMiddleware`
  construction, before the app is built. Keep the Host normalizer as harmless
  defense-in-depth.
- R3: Applies only to the HTTP path (`_run_http`); stdio untouched.

## Acceptance
- A1: After `docker compose up -d --build mcp`: POST /mcp -> 200/202 in mcp logs,
  chat answers, no 421.
- A2: py_compile clean; patch verified by simulation against the real SDK class
  semantics (settings=None -> protection off).

## Constraints
- Security rationale in code (internal docker network, gateway sole client).
- One file: mcp/master_orchestrator/main.py.
