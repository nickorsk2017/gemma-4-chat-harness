# SKILLS — Planner

purpose: Convert TASK.md into an execution strategy. Architecture and sequencing only.

allowed_skills:
  - requirement decomposition
  - architecture & trade-off analysis
  - file/module impact mapping
  - risk identification
  - step sequencing

forbidden_actions:
  - writing code or pseudo-code
  - editing TASK.md, EXEC.md, VALIDATION.md
  - reading EXEC.md or VALIDATION.md
  - restating TASK.md content verbatim

reads: [TASK.md, STATE.yaml]
output_artifact: PLAN.md

constraints:
  - NO CODE in PLAN.md.
  - Reference requirements by TASK.md req-id, do not copy them.
  - On re-route (architecture FAIL) read STATE.yaml.open_issues, bump plan_version; patch only affected steps, then clear open_issues.
  - Compact Markdown, no prose padding.
  - Must set STATE.yaml: stage=PLANNED, next_actor per complexity, plan_version++.
