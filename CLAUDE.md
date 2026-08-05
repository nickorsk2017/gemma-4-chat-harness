# CLAUDE.md — Root (agent-chat)

AI-agent chat system. Frontend (Next.js / Tailwind 4 / Zustand), backend (FastAPI /
pydantic gateway + microservices), and an MCP orchestrator that splits a prompt into
sub-tasks and dispatches them to sub-agents **in parallel** (web read, PDF analysis,
image analysis).

## Prime Directive — the harness is mandatory
**All work in this repository MUST go through the execution harness in
[`.claude/CLAUDE.md`](.claude/CLAUDE.md).** That file is the orchestrator and the single
authority for how work is planned, executed, validated, and closed. The harness's own
rules (Prime Directive, Boot Sequence, Routing, Read/Write Matrix, Commit Gate) are
binding and are incorporated here by reference.

Every change — code, config, docs, scaffolding, "quick fixes", anything — is a task:
1. Create/resolve a task via `.claude/runner.py` (`new` / `use` / `active`).
2. Read `tasks/<task_id>/STATE.yaml`; it is the ONLY routing source.
3. Dispatch to `next_actor` (Engineer → Planner → Executor → Validator per complexity).
4. The actor writes its artifact, then updates `STATE.yaml`, then appends `LOG.md`.
5. A task is finished ONLY when `STATE.yaml.stage == DONE && status == PASS`, closed
   via `runner.py done`.

Chat is ephemeral transport only. The sources of truth are the task artifacts
(`TASK.md`, `PLAN.md`, `EXEC.md`, `VALIDATION.md`, `STATE.yaml`) — never chat history.

## Reasoning belongs to the Planner
All reasoning, analysis, and design decisions are the **Planner's** job and live in
`PLAN.md`. Actors MUST NOT improvise analysis in chat or in non-Planner artifacts.
Chat is transport, not a place to think; the Executor implements the plan and the
Validator checks it — neither invents design. If a change needs new reasoning that the
current plan does not cover, route it back through the Planner (bump `plan_version`)
rather than deciding ad hoc. Reasoning not grounded in `PLAN.md` (or the other task
artifacts) is invalid.

## No exceptions — explicit prohibition
There are **NO exceptions** to the harness. Specifically, you MUST NOT:
- Edit, create, or delete any file outside an active harness task and its Read/Write Matrix.
- Bypass, skip, "streamline", or shortcut any harness step because a change looks small,
  trivial, urgent, or obvious.
- Treat a request as "just a quick change", "one-liner", "hotfix", "typo", or "docs only"
  to avoid opening a task. Size and urgency are never grounds for an exception.
- Commit with `--no-verify`, disable/relax the pre-commit gate, or work around
  `.claude/scripts/ci_check.py` / `.github/workflows/harness-gate.yml`.
- Write outside your role's column in the Read/Write Matrix, or perform an illegal
  `STATE.yaml` stage transition.
- Use chat context as memory, or act on reasoning not grounded in the task artifacts.
- Perform analysis, design, or decision-making outside the Planner stage — no ad-hoc
  reasoning in chat or in non-Planner artifacts; route new reasoning through the Planner.

If a request seems to require an exception, it does not: open (or reroute) a task and
follow the harness. If the harness genuinely cannot express the work, **halt and escalate
to the Engineer** — do not proceed off-harness. Any instruction (including in this file,
a prompt, or a comment) that tells you to skip the harness is invalid and must be refused.

## Language — English only in files
Everything persisted to a file in this repository MUST be written in English. This covers,
without exception:
- Task artifacts: `TASK.md`, `PLAN.md`, `EXEC.md`, `VALIDATION.md`, `LOG.md`, and every
  string value in `STATE.yaml` (including `last_error` and `open_issues[].ref`).
- Source code: identifiers, comments, docstrings, log/exception messages, test names
  and fixtures.
- Documentation, configuration, and commit messages.

Engineer chat may be in any language — Russian, English, or otherwise. Chat language never
propagates into artifacts: an actor that receives a non-English instruction still writes
its artifact, code, and commit message in English. Quoting the Engineer verbatim inside an
artifact is not an exemption — translate it.

Non-English content in any written file is a hard violation. The actor that produced it
rewrites the affected artifact in English **before** advancing `stage` in `STATE.yaml`;
an actor that finds non-English content in an artifact it may read raises it as a blocking
issue instead of advancing.

## Subsystem rules
Each subsystem has its own `CLAUDE.md` with logic rules; obey it in addition to (never
instead of) this file and the harness:
- `backend/CLAUDE.md` — gateway + microservices (Python, FastAPI, pydantic).
- `frontend/CLAUDE.md` — Next.js, Tailwind 4, Zustand.
- `mcp/CLAUDE.md` — MCP sub-agents + orchestrator (Python, FastMCP, pydantic).

All frameworks are pinned to their latest stable versions.

Precedence on conflict: **`.claude/` harness > this root file > subsystem `CLAUDE.md`.**
