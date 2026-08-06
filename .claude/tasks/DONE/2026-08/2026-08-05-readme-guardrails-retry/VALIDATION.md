# VALIDATION — 2026-08-05-readme-guardrails-retry
validation_version: 1

## v1
result: PASS

- A1: `## Guardrails` section present between `## Architecture` and
  `## Repository structure`; covers service purpose, checks, call-site coverage,
  and fail/retry policy (R1, R2). PASS.
- A2: Ports table contains `| guardrails | 8200 | ... |`. PASS.
- A3: `git status --porcelain` shows only `README.md` plus this task's own
  artifacts and `.claude/tasks/ACTIVE`; no other file touched. PASS.
- A4: Valid Markdown (headings/table syntax consistent with rest of file),
  English-only. PASS.

No issues.
