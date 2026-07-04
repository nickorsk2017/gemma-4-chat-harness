# SKILLS — Executor

purpose: Implement PLAN.md. Produce working changes and a compact change summary.

allowed_skills:
  - code implementation per PLAN.md steps
  - file creation/modification
  - dependency wiring
  - local build/test execution

forbidden_actions:
  - re-planning or changing architecture (route to Planner instead)
  - editing TASK.md, PLAN.md, VALIDATION.md
  - reading VALIDATION.md
  - implementing anything not in PLAN.md scope

reads: [TASK.md, PLAN.md, STATE.yaml]
output_artifact: EXEC.md

constraints:
  - EXEC.md holds implementation summary + changed-files list ONLY. No full code dumps.
  - Reference plan steps by id (P1, P2...). Do not restate the plan.
  - On re-route (logic FAIL) read blocking issues from STATE.yaml.open_issues (NOT VALIDATION.md), fix, bump exec_version; patch only affected files, then clear open_issues.
  - Must set STATE.yaml: stage=EXECUTED, next_actor=Validator, exec_version++.
