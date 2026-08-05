# VALIDATION — 2026-08-03-image-analyzer-output-gate

## v1

result: FAIL
issues: [V1]

### Acceptance
| Id | Evidence | Verdict |
|---|---|---|
| A1 | `test_allowed_answer_is_returned_unchanged` passes; service returns `answer` verbatim and the gate saw the same string with `source="image_analyzer"` | PASS |
| A2 | `test_blocked_answer_becomes_the_refusal_and_echoes_nothing` + `test_blocked_answer_is_not_an_agent_failure` pass; `answer == IMAGE_REJECTED`, no fragment of the model text, envelope stays `Status.OK` (tools/ unmodified) | PASS |
| A3 | `test_allowed_verdict_never_rewrites_the_answer` passes with a rewritten `text` + non-empty `redactions` present in the verdict | PASS |
| A4 | `test_unreachable_gate_releases_the_answer_and_logs_the_incident` passes against a dead port using the real `check_output`; answer released, `ungated` + `source=image_analyzer` in the ERROR record | PASS |
| A5 | new suite 5/5; `test_gate_outage.py` + `test_guardrail_gates.py` 20/20 combined. The 2 failures in `test_doc_analyzer_gate.py` reproduce independently of this task: its stub is `_check_input(text, *, source, thread_id=None)` (lines 63, 76) and `doc_analyzer/services/analyze_service.py:62` passes `surface=` — neither file is in this task's write set | PASS (pre-existing failures noted, out of scope) |
| A6 | Verified by inspection, not `git diff` — the tree was dirty before the task opened and `agent_core/guardrails.py` + `mcp/tests/` are untracked, so a diff proves nothing either way. `agent_core/guardrails.py` carries exactly one added block (`IMAGE_REJECTED`, L263-267); `doc_analyzer/`, `web_agent/`, `master_orchestrator/` unmodified by this task | PASS |

### Requirements
R1 ✓ (`check_output(answer, source="image_analyzer")`, L60) · R2 ✓ (service, between flatten
and construction) · R3 ✓ (constant in `agent_core`, no literal in the agent) · R4 ✓ (only
`.allowed` and `.categories` read; `.text`/`.notice`/`.redactions` unread) · R5 ✓ (no raise, no
`tools/` change) · R6 ✓ (no try/except, no local retry or timeout) · R7 ✓ (fields mirror
`doc_analyzer/config.py`, aliases and defaults identical, not passed into the call) · R8 ✓
(`image_analyzer/pyproject.toml` unchanged; `agent-core` was already a dependency).

### Issues

**V1** — type: `architecture` · severity: high · ref: PLAN R-1, TASK R6 · status: blocking

PLAN R-1 instructed this stage to check the outage worst case against the gateway timeout and
raise it rather than absorb it. It does not clear.

The plan's own estimate ("2 x deadline") undercounts. The ladder is paid **per gate call**, and
`analyze_image` is a tool inside the orchestrator's loop, which runs up to
`max_tool_iterations = 4` rounds and re-dispatches whatever tools the model asks for — nothing
dedupes a repeated call. With default env (`ATTEMPTS=4`, `TIMEOUT_S=10`, `BASE=1`, `FACTOR=2`)
one ladder costs ~47s (4 x 10s of dead-port timeout + 1+2+4s of backoff), capped at the 60s
`OUTPUT_DEADLINE_S`.

- worst case before this task: 1 ladder (merge gate) ≈ 47s
- worst case after: N image-tool calls + merge, N ≤ 4 → up to 5 x 47 ≈ 235s
- `gateway.orchestrator_timeout_s` = 180.0 (`backend/_common/env/settings.py:58`)

Two image calls in one turn already put it at ~141s before the vision and merge LLM calls are
counted. So during a gate outage the turn can now exceed the gateway's hard timeout and the
user gets a transport error — losing the very answer the fail-open policy exists to release.
The task converts a bounded degradation into an unbounded-enough one.

Not a logic defect: the Executor implemented the plan, and R6 explicitly forbade a local
timeout, retry or catch. The unowned decision is where the ladder belongs when the call site is
inside a loop — which is a Planner question, hence `architecture`, hence a `plan_version` bump
rather than an `exec_version` one.

Directions the Planner may consider (not prescriptions): a per-turn/per-process gate-outage
circuit breaker so the first exhausted ladder makes subsequent calls cheap; single-shot at this
call site with the ladder left to the merge gate only (the merge still gates the same content);
or an explicit deadline budget shared across gate calls within one turn. Any of these changes
the policy owner, so it cannot be decided here.

### Non-blocking notes
- N1: the blocked branch logs `verdict.categories`. The gate returns `blocked` both on a policy
  hit and on its own model being unavailable (see `_gate_result`'s comment in the orchestrator),
  so an empty category list in this log means "outage", not "clean". Worth a comment, not a fix.
- N2: verification ran on python 3.10 in a Linux sandbox, not the pinned `>=3.12,<3.14` — the
  repo's `mcp/.venv` is a macOS venv and does not execute in this session. Nothing added uses
  post-3.10 syntax, but the pinned interpreter remains unexercised for this change.

## v2

result: FAIL
validation_version: 2
issues: [V2, V3]

Scope of this pass: EXEC v2 (steps P6-P10) against TASK as amended v3 + v4. The v1 findings
stand — the image gate itself (P1-P5, A1-A5) is unaffected by the amendments and remains PASS.

### State of the three declaration sites (R13, R15, A10)
| Var | `agent_core/guardrails.py` | `docker-compose.yml` | `mcp/.env.example` | required (A10) |
|---|---|---|---|---|
| `GUARDRAILS_TIMEOUT_S` | 10 | 10 | 10 | **15** |
| `GUARDRAILS_RETRY_ATTEMPTS` | 4 | 2 | 2 | 2 |
| `GUARDRAILS_RETRY_BASE_S` | 1 | 1 | 1 | 1 (PLAN's call) |
| `GUARDRAILS_RETRY_FACTOR` | 2 | 2 | 2 | **1** |
| `GUARDRAILS_OUTPUT_DEADLINE_S` | 60 | 22 | 22 | per R14/R18 |

No site satisfies A10, and the code column disagrees with the other two on two rows — which is
exactly the C1 the Executor raised, now a requirement violation rather than a conflict.

Also unsatisfied: R14 is already violated at the *current* values if R12 lands, since a 22 s
deadline sits below the 31 s ladder that 15 s per attempt produces.

### Issues

**V2** — type: `architecture` · severity: high · ref: TASK amendment v4 (R11/A7 withdrawn) ·
blocking. PLAN v2's D11 and its turn table are the accounting the Engineer withdrew, and PLAN
v1's R-1 risk is written against the same superseded model. Amendment v4 requires D11 be
*deleted* with a recorded reason, not updated. Until PLAN is re-cut, no downstream artifact has
a valid budget to implement against. Planner bumps `plan_version` and sets `DEADLINE` and the
gap from R16/R17.

**V3** — type: `logic` · severity: medium · ref: R12, R13, R15, R17, A10 · blocking. EXEC v2
implemented the pre-amendment values. Five rows across three files need moving, and the
`agent_core` defaults are now explicitly in scope (amendment v3 lifted R10's prohibition for
exactly these). `tests/test_gate_budget.py` asserts the old 21 s ladder and the old 10 s floor;
both assertions must be re-derived from the new values — re-derived, not relaxed (A9).
Follows V2: the values come from the re-cut plan.

### Routing note
Type priority puts `architecture` (V2) ahead of `logic` (V3), so the work belongs to the
Planner. These are not defects in the delivered work — EXEC v2 matched the plan it was given,
and both issues exist because the requirements changed underneath it. That distinction does not
change the routing, but it belongs in the record.

Loop control: this is the second FAIL re-route, `iteration` reaches `max_iterations` (2), so the
harness escalates to the Engineer rather than dispatching the Planner directly.

## v3

result: FAIL
validation_version: 3
issues: [V4, V5]

Scope: EXEC v3 against TASK v6 (R22/R24 as clarified) and PLAN v3+v4. Verified by running
and reading, not by reading EXEC.

### Acceptance
| Id | Evidence | Verdict |
|---|---|---|
| A1-A4 | image-gate suite 5/5; unchanged since v1 | PASS |
| A5 | `test_gate_budget.py` with the env cleared: attempts 2, factor 1, ladder 31.0 s, deadline 35 > 31 | PASS |
| A6 | 15 / 2 / 1 / 1 / 35 identical in `agent_core/guardrails.py`, `docker-compose.yml`, `mcp/.env.example` | PASS |
| A7 | `LLM_REQUEST_TIMEOUT_S=30` in compose, Makefile, both `.env.example`; gateway 66 in `settings.py`, compose, Makefile (both recipes). The ~66 s abort itself is not demonstrated — no stack was run | PARTIAL |
| A8 | `error_code` on `ApiResponse`, forwarded from envelope `meta.code`, and set on the gateway's own `TimeoutError` branch; router maps it to 504 | PASS |
| A9-A10 | code present and type-checked; behaviour not exercised — see V5 for a defect found by reading it | PARTIAL |
| A11 | table below | PASS |
| A12 | 31 passed; the 2 `test_doc_analyzer_gate.py` failures reproduce independently (stub omits `surface`) | PASS |
| A13 | `grep -rn ORCHESTRATOR_SUBAGENT_TIMEOUT_S` over compose, Makefile, both `.env.example`, `mcp/` -> nothing | PASS |
| **A8 (the R1-R8 one)** | **fails as written — see V4** | **FAIL** |

Note: TASK v6 numbers two different acceptance criteria `A8`. The table above reads the
gate-block one as "the typed outcome"; the requirements-block one is V4.

### Budget containment, per call (A11)
| Inside | Value | Container | Value | Holds |
|---|---|---|---|---|
| one LLM attempt | 30 s | turn | 60 s | yes |
| one gate call (2 x 15 + 1) | 31 s | turn | 60 s | yes |
| gate phase deadline | 35 s | turn | 60 s | yes |
| turn | 60 s | gateway request | 66 s | yes |
Identical in both stacks: compose and Makefile declare the same four numbers, and with
nothing declared the code defaults reproduce them (`test_gate_budget.py`).

### Issues

**V4** — type: `requirement` · severity: medium · ref: TASK A8 (requirements block) ·
blocking. A8 forbids modifying any file under `backend/`, while R15, R17 and R20 cannot be
satisfied without modifying `backend/_common/env/settings.py`, `backend/_common/schemas/
response.py` and three files under `backend/gateway/`. The criterion survived from the
version of this task that ended at the gate's budget and was not re-cut when the ceiling
and the retry were folded in. It is unsatisfiable as written, so it cannot be judged PASS,
and the Executor was right to proceed rather than stall on it.

Second, smaller half: `mcp/doc_analyzer/config.py` was modified (its `guardrails_timeout_s`
mirror, 10 -> 15). R14 names three declaration sites and that file is not one of them.
Leaving it at 10 would have left a mirror contradicting the value it mirrors, so the edit
is defensible — but it is outside the stated write surface and needs to be either
sanctioned or reverted, not left ambiguous. `web_agent/` and `image_analyzer/` carry the
same mirror; `image_analyzer/` was updated, `web_agent/` has none.

Engineer edit only: re-cut A8 to name what this task is actually allowed to touch.

**V5** — type: `logic` · severity: medium · ref: R18, R19, A10 · blocking. The retry button
survives a page reload; the request it would re-send does not. `partialize` persists
`messages` (including the entry carrying `retryable: true`) but deliberately not `pending`,
which holds the prompt and files. After a reload the transcript still shows "Повторите
запрос" with a working-looking button, and `retry()` returns immediately on `!pending` —
a control that does nothing, in the one place the user was invited to act.

Either the placeholder must not be persisted, or the prompt must be (files cannot be, which
is presumably why `pending` was excluded), or the button must be disabled when `pending` is
null. Any of the three closes it; the choice is the Executor's within PLAN D22.

### Non-blocking notes
- N3: verification ran on python 3.10; the repo pins >= 3.12. `asyncio.wait_for` was chosen
  partly for that reason (EXEC v3 deviation 1) — reasonable, and worth re-running on the
  pinned interpreter before release.
- N4: A7's and A9/A10's behavioural halves need a live stack. They are marked PARTIAL rather
  than PASS so the gap is visible in the record.
- N5: `mcp/master_orchestrator/config.py` now carries a stray double blank line before the
  guardrails block and lost the trailing blank line before `settings = ...`. Cosmetic.

## v4

result: PASS
validation_version: 4
issues: []

Scope: EXEC v4 against TASK v6 (R25/A14/A15 included, V4 withdrawn by the Engineer) and
PLAN v3+v4.

### V5 — closed
`partialize` filters `retryable` entries (`chatStore.ts:216`), so the offer to re-send dies
with the session while the conversation survives. The failed turn's user message is kept
deliberately and that is the right call: the question was asked, and hiding it would
misrepresent the transcript more than showing it unanswered.

The `instanceof` defect the Executor found while closing V5 is real and was worth the
detour. The store now matches on `code` duck-typed (`chatStore.ts:16-22`). Confirmed by
reading the existing suite: `__tests__/chatStore.test.ts` mocks `@/services/chatService`
with a factory exporting two functions, so `ChatServiceError` would have been `undefined`
inside every store test and the error branch would have thrown. The type checker cannot see
this, and neither could a green `tsc` — it was found by reading, which is the only tool
that was available for it here.

### Acceptance
| Id | Evidence | Verdict |
|---|---|---|
| A1-A4 | image-gate suite 5/5 | PASS |
| A5 | env cleared: attempts 2, factor 1, ladder 31.0 s, deadline 35 | PASS |
| A6 | 15/2/1/1/35 identical in `agent_core/guardrails.py`, compose, `mcp/.env.example` | PASS |
| A7 | 30 / 60 / 66 at every declaration site; the ~66 s abort itself unrun (see limits) | PASS (code), unverified (behaviour) |
| A8 | `error_code` on the envelope, forwarded from `meta.code`, set on the gateway's own timeout branch, mapped to 504 | PASS |
| A9, A10, A14 | four store tests written and type-checked; unrun (see limits) | PASS (code), unverified (behaviour) |
| A11 | table in v3; unchanged | PASS |
| A12 | 31 passed; the 2 `doc_analyzer` failures pre-date the task and reproduce independently | PASS |
| A13 | grep returns nothing outside task artifacts | PASS |
| A15 | `guardrails_timeout_s = 15.0` in all three sub-agent configs | PASS |

### Constant parity (checked because it is the contract, and it is duplicated by design)
`"turn_timeout"` in `orchestrator.py:49`, `agent_client.py:28` (mirrored, not imported —
backend rule 7), `chat.d.ts:52`, `chatService.ts:75`, `chatStore.ts:21`. Five copies, all
equal. This is the price of the no-cross-import rule and is the thing most likely to drift;
`agent_client.py` carries the comment that says so.

### Limitations — what a PASS here does and does not mean
Nothing behavioural was executed. Two independent reasons, both environmental:
- `mcp/.venv` is a macOS venv; the Python suite ran on a sandbox 3.10 against PyPI installs,
  while the repo pins >= 3.12.
- `jest` cannot start at all: the Next SWC binary in `node_modules` is darwin, the sandbox is
  linux/arm64.

So A7's abort, A9/A10's rendering and press, and A14's reload are verified as code and not
as behaviour. Before this ships, on the host:
1. `cd frontend && pnpm test` — the four new store cases.
2. `make up`, then a turn that exceeds the budget: expect ~66 s, HTTP 504 with
   `error_code: "turn_timeout"`, the retry entry, a working button, and after a reload no
   button.
3. `cd mcp && pytest` on the pinned interpreter.

A PASS on the artifacts is not a claim that the stack was watched doing this.
