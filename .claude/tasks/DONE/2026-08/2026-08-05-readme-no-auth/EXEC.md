# EXEC — 2026-08-05-readme-no-auth
exec_version: 1

## v1

### Change
`README.md`: new section `## Status: demo — no authentication, no authorization`
inserted immediately above `## Quick start` (R3). Two paragraphs: what is absent
(authn + authz, no user/session/thread ownership, `thread_id` identifies but does not
protect) per R1, then the consequence on an exposed deployment — LLM budget spent on
the repo owner's keys, any thread readable and deletable by its id — plus the
mitigation available today (localhost or an authenticating proxy) per R2. No roadmap,
no promise of a fix (R4).

### Scope
One file, docs only. No code, config, dependency or task-artifact changes elsewhere (A3).
No mention of rate limiting: task 2026-08-05-rate-limit is open and unshipped.

### Verification
- A1/A2: section present, above Quick start, covering both authn and authz + consequence.
- A3: `git status --porcelain` shows README.md plus this task's own artifacts only.
- A4: heading level fits the file's existing structure; English only.
