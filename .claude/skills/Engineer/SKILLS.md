# SKILLS — Engineer (Human Operator)

purpose: Define requirements, approve plans, resolve escalations. System operator.

allowed_skills:
  - author/edit immutable requirement (TASK.md)
  - approve HIGH-complexity plans
  - resolve requirement-type failures
  - handle escalations (iteration > max)

forbidden_actions:
  - editing PLAN.md, EXEC.md, VALIDATION.md
  - bypassing STATE.yaml routing

reads: [all]
writes: [TASK.md, STATE.yaml]

constraints:
  - TASK.md is immutable once stage advances past INIT, except on requirement-type FAIL or ESCALATED.
  - Approval = set STATE.yaml stage=APPROVED, next_actor=Executor.
  - Escalation resolution = edit TASK.md and/or reset iteration=0, then re-dispatch.
