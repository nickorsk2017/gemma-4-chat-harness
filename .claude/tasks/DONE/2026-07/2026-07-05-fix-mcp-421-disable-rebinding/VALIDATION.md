# VALIDATION — 2026-07-05-fix-mcp-421-disable-rebinding

## v1 (validates EXEC v1 against TASK)

- R1/R2: PASS — patch targets the exact class that emits 421 (source-verified
  semantics); works for any fastmcp-internal settings; uses only the SDK's
  public settings type. Not guess-based, unlike the Host rewrite alone.
- R3: PASS — patch invoked only from `_run_http()`; stdio path identical.
- A2: PASS — py_compile clean; simulation: 421 impossible post-patch, repro
  failed pre-patch (positive + negative control).
- A1: HOST-SIDE — rebuild required (`docker compose up -d --build mcp`); expected
  mcp log: `POST /mcp HTTP/1.1" 200` (or 202/406 handshake codes), no 421.
- Constraint (1 file): PASS — only main.py touched.

### Verdict
PASS — no open issues.
