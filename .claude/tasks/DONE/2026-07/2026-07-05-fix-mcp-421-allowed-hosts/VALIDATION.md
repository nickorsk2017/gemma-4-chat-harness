# VALIDATION — 2026-07-05-fix-mcp-421-allowed-hosts

## v1
- R1: PASS — two independent paths admit `mcp:8100` on fastmcp 3.4.3: the
  `allowed_hosts` kwarg (when `http_app` exposes it) and the DEFAULT_HOSTS
  extension (works regardless; matches the guard source the Engineer dumped
  from the running container: `_allowed_hosts_for_scope` starts from
  DEFAULT_HOSTS).
- R2: PASS — hosts are env-config (`ORCHESTRATOR_HTTP_ALLOWED_HOSTS`), defaults
  match compose identity.
- R3: PASS — TypeError fallback + no-op guards; 2.x layers retained.
- R4: PASS — stdio branch untouched.
- A2: PASS — py_compile + stub simulation (extension, idempotency, no-op).
- A1: HOST-SIDE — rebuild and send a message; expect 2xx on POST /mcp.

### Verdict
PASS — no open issues.
