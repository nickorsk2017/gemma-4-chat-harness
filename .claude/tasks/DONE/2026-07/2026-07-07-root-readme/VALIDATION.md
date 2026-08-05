# VALIDATION — 2026-07-07-root-readme

## v1 — PASS
- A1 PASS: README.md at root; covers overview / architecture / structure /
  harness / run / env / healthcheck / ports.
- A2 PASS: cross-checked — make targets match `grep '##' Makefile` (11 targets),
  ports match compose defaults (3000/8000/8100, postgres internal), env keys
  match .env.example (GEMMA_API_KEY, TAVILY_API_KEY required; LANGSMITH/ports/
  timeouts optional), harness description matches .claude/CLAUDE.md (roles,
  routing, max_iterations=2, DONE&&PASS closure).
- R2 PASS: states Novita provider + GEMMA_MODEL override + Tavily search.
