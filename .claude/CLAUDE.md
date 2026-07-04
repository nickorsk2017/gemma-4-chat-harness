# CLAUDE.md — Orchestrator

Deterministic, artifact-driven execution harness. Not a chatbot.

## Prime Directive
Chat = ephemeral transport only. The ONLY sources of truth are the task artifacts:
`TASK.md`, `PLAN.md`, `EXEC.md`, `VALIDATION.md`, `STATE.yaml`.
Reasoning that is not grounded in these files is invalid. Never use chat history as memory.

## Boot Sequence (every invocation)
1. Resolve active `task_id` via `runner.py active` (reads `tasks/ACTIVE`).
2. Read `tasks/<task_id>/STATE.yaml` -> this is the ONLY routing source.
3. Read the artifact(s) the `next_actor` is allowed to read (see matrix).
4. Dispatch to `next_actor` using its `skills/<Role>/SKILLS.md`.
5. Actor writes its output artifact, then updates `STATE.yaml`, then appends `LOG.md`.
   Order is fixed. On resume, if `STATE.yaml` and the last artifact disagree, trust
   the artifact and re-derive state (see Crash Recovery).
6. Halt. One actor per invocation. No chaining in memory.

## Runner (deterministic dispatch)
`runner.py` is the task registry + router. It never decides content — only routing.
- `runner.py new <id> [--complexity LOW|MEDIUM|HIGH]` scaffold a task, make it active
- `runner.py list`            all tasks: stage/status/next_actor (active marked `*`)
- `runner.py use <id>`        Engineer switches the active task
- `runner.py status [id]`     key STATE fields
- `runner.py next [id]`       print dispatch descriptor for `next_actor`
- `runner.py done [id] [--force]`  close a DONE task, clear active, signal safe-to-clear
- `runner.py install-hooks`   set core.hooksPath -> .claude/githooks (pre-commit gate)
Active task is stored in `tasks/ACTIVE`. Multiple tasks coexist; each has its own
STATE.yaml. The Engineer may switch freely without losing any task's state.

## Commit Gate & Task Closure
A task is finished only when `STATE.yaml.stage == DONE && status == PASS` — never by
a subjective yes/no. `runner.py done` verifies that, clears `tasks/ACTIVE`, and prints
that the chat window is safe to clear (context holds no truth; artifacts do). The
`.claude/githooks/pre-commit` gate blocks a commit when the active task is `ESCALATED`,
has non-empty `open_issues`, or is `DONE` (must be closed via `done` first). Mid-task
WIP commits pass. The Claude context window cannot be cleared by a script — the hook
only signals when it is safe to `/clear`.

Local hooks are advisory (a dev can `--no-verify`). Server-side, `.claude/scripts/ci_check.py`
re-checks repo-wide invariants (no ESCALATED task, no non-empty open_issues, DONE=>PASS)
and is run by `.github/workflows/harness-gate.yml` on push/PR — that gate is not
bypassable and is the authoritative barrier.

## Crash Recovery
Writes are sequential, not transactional. If an invocation died mid-step:
- artifact written but `STATE.yaml` not advanced -> re-run the STATE update only.
- `STATE.yaml` advanced but `LOG.md` missing the line -> append the log line only.
Never re-run an actor's content step that already produced its artifact for this version.

## Roles
- Engineer = human operator (writes TASK.md, approvals)
- Planner  = architecture & strategy -> PLAN.md
- Executor = implementation -> EXEC.md
- Validator = quality gate -> VALIDATION.md

## Complexity Classification
On first read of TASK.md, set `complexity`:
- LOW    -> Engineer -> Executor -> Validator
- MEDIUM -> Engineer -> Planner -> Executor -> Validator
- HIGH   -> Engineer -> Planner -> Engineer(approve) -> Executor -> Validator

Heuristic (estimate from TASK.md scope, not from a prior plan):
files_touched<=1 & no new deps -> LOW; multi-file / new module -> MEDIUM;
cross-cutting / schema / infra / security -> HIGH.
If a LOW task turns out to touch >1 file during execution, Validator raises an
`architecture` issue and the task is re-routed through Planner at MEDIUM.

## Routing (state machine)
```
stage: INIT       -> next_actor: Planner (MED/HIGH) | Executor (LOW)
stage: PLANNED    -> next_actor: Engineer (HIGH approval) | Executor
stage: APPROVED   -> next_actor: Executor
stage: EXECUTED   -> next_actor: Validator
stage: VALIDATED  -> status PASS: DONE | status FAIL: see Failure Routing
stage: DONE       -> halt
stage: ESCALATED  -> next_actor: Engineer
```

## Failure Routing (VALIDATION = FAIL)
On FAIL the Validator MUST copy every blocking issue into `STATE.yaml.open_issues`
(each: {id, type, severity, ref}). This is the sanctioned handoff: downstream actors
read issues from `STATE.yaml` (which they may read), NOT from `VALIDATION.md`.

Route by issue `type` priority (highest first), independent of `severity`:
1. `requirement`  -> Engineer (halt for TASK.md edit)
2. `architecture` -> Planner (bump plan_version)
3. `logic`        -> Executor (bump exec_version)

`severity` only orders issues WITHIN the same type and for reporting; it never
overrides type priority. The chosen actor clears `open_issues` once addressed.

## Loop Control
`max_iterations = 2` (from SETTINGS.md) = number of FAIL re-routes allowed.
On each FAIL re-route: `iteration += 1`.
If `iteration >= max_iterations` after the increment -> set `stage: ESCALATED`,
`next_actor: Engineer`, write `last_error`. (max=2 => attempts at iteration 1 and 2,
escalate on the 2nd unresolved FAIL.)

## Write Discipline
- Incremental updates only; never rewrite a full artifact unless structurally required.
- No prose, no restated context, no duplicated info across artifacts.
- Versioned artifacts (PLAN/EXEC/VALIDATION) keep prior versions as appended
  `## v<n>` blocks so diffs/rollback survive; do not delete old version blocks.
- Every actor MUST update `STATE.yaml` and append one line to `LOG.md`.

## Read/Write Matrix (enforced)
| Actor     | Read                                    | Write                     |
|-----------|-----------------------------------------|---------------------------|
| Engineer  | all                                     | TASK.md, STATE.yaml       |
| Planner   | TASK.md, STATE.yaml                     | PLAN.md, STATE.yaml       |
| Executor  | TASK.md, PLAN.md, STATE.yaml            | EXEC.md, STATE.yaml       |
| Validator | TASK.md, PLAN.md, EXEC.md, STATE.yaml   | VALIDATION.md, STATE.yaml |

Note: Executor/Planner receive validation feedback via `STATE.yaml.open_issues`,
never by reading `VALIDATION.md`. Any write outside a role's column is a hard
violation -> abort, do not mutate state. Enforced at runtime by
`.claude/hooks/enforce_matrix.py` (PreToolUse on Write|Edit): enforces the write
matrix AND legal `stage` transitions on every STATE.yaml write.
