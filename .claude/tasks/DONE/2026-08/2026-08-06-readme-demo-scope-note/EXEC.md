# EXEC — 2026-08-06-readme-demo-scope-note
exec_version: 1

## v1
- Rewrote the "Status: demo — no authentication, no authorization" section in
  README.md.
- Added: explicit statement that the repo's purpose is to demonstrate the
  execution harness (`.claude/`) and the multi-agent MCP orchestration system,
  and that auth/authorization is intentionally out of scope for that purpose
  (deliberate choice, not an oversight) so setup stays `cp .env.example .env &&
  make up` with no accounts/sessions/login flows.
- Preserved: no-user/no-session/no-owner description, open-endpoint exposure,
  thread_id-is-not-a-credential framing, LLM budget/read/delete risk, and the
  "run on localhost or behind your own authenticating proxy" guidance.
- Files changed: README.md only.
