# TASK — 2026-08-06-readme-demo-scope-note
owner: Engineer
immutable: true

## Requirements
- R1: Update the "Status: demo — no authentication, no authorization" section in
  README.md to explicitly state that this project's purpose is to demonstrate the
  execution harness (`.claude/`) and the multi-agent MCP orchestration system, and
  that auth/authorization is intentionally out of scope for that purpose — not a
  gap to be filled — so it does not add setup steps for someone running the code.

## Acceptance
- A1: README.md's demo-status section states in English that the project's purpose
  is to demonstrate the harness and multi-agent system.
- A2: The section states that authentication/authorization is intentionally out of
  scope (by design, not an oversight), and explains this keeps setup simple for
  whoever runs the code.
- A3: The existing concrete risk description (open endpoints, thread_id is not a
  credential, LLM budget/read/delete exposure) and the "run on localhost or behind
  your own authenticating proxy" guidance are preserved.
- A4: No other files change.

## Constraints
- English only, per root CLAUDE.md language rule.
- Single file (README.md) — stays LOW complexity.
