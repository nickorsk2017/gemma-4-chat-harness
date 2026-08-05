# VALIDATION — 2026-08-05-readme-no-auth
validation_version: 1
result: PASS

## v1

### Requirement checks
- A1 PASS — `## Status: demo — no authentication, no authorization` sits between the
  repository-structure table and `## Quick start`; a reader meets it before any run
  instruction (R3).
- A2 PASS — the section names both missing controls (authn and authz: no user, no
  session, no thread ownership) and the R2 consequence (LLM budget spent on the
  owner's keys; any thread readable or deletable by its id). It also states what a
  reader can do today (localhost / own authenticating proxy), which is mitigation,
  not a promised fix (R4).
- A3 PASS for this task — the only file this task touched is `README.md`; its diff is
  a pure 11-line insertion, no other hunk.
- A4 PASS — heading level matches the file's existing `##` sections; English only.

### Observation (non-blocking, out of this task's scope)
The working tree carries unrelated uncommitted changes, including a full
implementation of the rate limiter designed in task `2026-08-05-rate-limit`
(`backend/_common/ratelimit.py`, `backend/gateway/middleware/`,
`mcp/agent_core/ratelimit.py` plus edits across gateway, orchestrator and frontend)
that appeared while `2026-08-05-rate-limit` was still at `stage: PLANNED` awaiting
Engineer approval. That task's STATE therefore contradicts the tree. It is raised
here for the Engineer, not as an issue against this task: this task's requirements
and diff are unaffected, and none of that code claims anything about authentication.
