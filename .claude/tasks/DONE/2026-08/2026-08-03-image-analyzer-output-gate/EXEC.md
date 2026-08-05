# EXEC — 2026-08-03-image-analyzer-output-gate

## v1 — P1-P5 complete

### Changed

| File | Change | Plan step |
|---|---|---|
| `mcp/agent_core/guardrails.py` | `IMAGE_REJECTED` added after `DOCUMENT_REJECTED`; nothing else touched | P1 |
| `mcp/image_analyzer/config.py` | `guardrails_url` / `guardrails_timeout_s`, same defaults and aliases as `doc_analyzer/config.py` | P2 |
| `mcp/image_analyzer/services/analyze_service.py` | gate call after the flatten, block branch, one `warning` log, docstring carrying D1-D5 | P3 |
| `mcp/tests/test_image_analyzer_gate.py` | new, 5 cases | P4 |
| `mcp/image_analyzer/tools/analyze_image.py` | **untouched**, per D3 | — |

### Implementation notes (deviations and judgement calls only)

- **P1 wording.** The constant names no category, per P1's own instruction. It reads
  "This image cannot be described: the description violates the service's terms of use."
  — the refusal is about the *description*, not the picture, which is what the output
  verdict actually judged.
- **P3, log line.** Logs `filename` and `verdict.categories`, never the answer. The answer
  is the thing the gate just refused to release; putting it in a log moves it rather than
  withholds it.
- **P4, five cases not four.** A2 splits: one case asserts the constant and the absence of
  the model's wording, a second asserts the blocked answer is still a normal
  `ImageAnalysis` carried by `AgentResponse.ok` (R5). These are different claims — the
  first would pass under an implementation that raised and produced an error envelope.
- **P4, A4 stub scope.** As planned, the real `check_output` runs against a dead port
  (`127.0.0.1:9`) with the ladder clamped to 1 attempt; the fail-open verdict is the
  client's own. The assertion also checks the incident carries `source=image_analyzer`.
- Import form is `from agent_core.guardrails import IMAGE_REJECTED, check_output`, so the
  tests patch `analyze_service.check_output` (R-4 closed by construction).

### Verification

Run in a Linux sandbox venv (py3.10, deps installed from PyPI) — **not** the repo's
`mcp/.venv`, which is a macOS venv and does not execute here.

- `pytest tests/test_image_analyzer_gate.py` -> **5 passed** (A1-A4).
- `pytest tests/` -> **20 passed, 2 failed**. Both failures are in
  `tests/test_doc_analyzer_gate.py` and are **pre-existing**: its stub is
  `async def _check_input(text, *, source, thread_id=None)` (lines 63, 76) while
  `doc_analyzer/services/analyze_service.py:62` calls `check_input(..., surface="document")`
  — a stub that was never updated when `surface` became a parameter. Neither file is
  touched by this task. `test_gate_outage.py` and `test_guardrail_gates.py` pass.
- Interpreter caveat: the repo pins `>=3.12,<3.14`; the sandbox ran 3.10. Nothing added
  here uses post-3.10 syntax, but the run is not on the pinned interpreter.

### A6 — cannot be checked with a bare `git diff`

The working tree was **already dirty when this task opened**: `git status` shows
pre-existing modifications across `frontend/`, `backend/`, `docker-compose.yml`,
`master_orchestrator/`, `doc_analyzer/services/analyze_service.py`, and `mcp/tests/` and
`mcp/agent_core/guardrails.py` are untracked in their entirety. A repo-wide `git diff`
therefore reports files this task never opened, and `mcp/agent_core/guardrails.py` shows
no diff at all because it is untracked.

Scoped to the files this task touched, A6 holds: the only edits are the four table rows
above, `agent_core/guardrails.py` gained the constant and nothing else, and no file under
`doc_analyzer/`, `web_agent/` or `master_orchestrator/` was opened for writing. The
Validator should verify by inspection of those files, not by `git diff --name-only`.

### Not done

Nothing deferred. R-1 (the double ladder, up to 2 x `GUARDRAILS_OUTPUT_DEADLINE_S` on a
gate outage) is untouched by design — R6 forbids a local fix — and is left for the
Validator to weigh against the gateway timeout, as PLAN R-1 asks.

## v2 — PLAN v2 steps P6-P10 (closes V1, surfaces a requirement conflict)

### Changed

| File | Change | Plan step |
|---|---|---|
| `mcp/master_orchestrator/config.py` | `max_tool_iterations` 4 -> 2, comment states it is a gate-budget input | P6 (R9) |
| `docker-compose.yml` | `GUARDRAILS_RETRY_ATTEMPTS` 4 -> 2, `GUARDRAILS_OUTPUT_DEADLINE_S` 60 -> 22 | P7 (R10) |
| `docker-compose.yml` | the "Four attempts ... 47s worst case" comment replaced with D10/D11's numbers, incl. why `GUARDRAILS_TIMEOUT_S` stays 10 and what the shortened ladder costs | P9 |
| `mcp/.env.example` | all four ladder vars added (only URL + TIMEOUT were documented); timeout comment now names the 8s judge budget | P8 (A8) |
| `mcp/tests/test_gate_budget.py` | new: the three numbers D11 rests on | P10 |

Deviation from P10: the loop-bound assertion targets the *declared default*
(`OrchestratorSettings.model_fields[...].default`) rather than an instance, so a stray local
`.env` cannot make it pass for the wrong reason. It also lives in its own module — nothing in
it is async, and the image suite's module-level asyncio mark would have applied to it wrongly.

### Verification

- `tests/test_image_analyzer_gate.py`, `tests/test_gate_outage.py`, `tests/test_guardrail_gates.py`
  -> **21 passed**.
- `docker-compose.yml` parses; the mcp service's guardrails env reads
  `ATTEMPTS=2`, `BASE=1`, `FACTOR=2`, `DEADLINE=22`, `TIMEOUT_S=10`.
- `tests/test_gate_budget.py` -> **2 passed, 1 failed**, deliberately. See below.
- `test_doc_analyzer_gate.py`'s 2 failures are the same pre-existing stub mismatch reported in
  v1, unchanged by this step.

### C1 — the failing test is the finding, not a defect to patch out

`test_ladder_defaults_produce_a_21_second_worst_case` computes the ladder from
`agent_core.guardrails`'s own defaults with the env cleared, and gets **47 s, not 21 s**.

P7/P8 moved the *declared* values in compose and `mcp/.env.example`. The **code** defaults in
`agent_core/guardrails.py` are still `ATTEMPTS=4` / `DEADLINE=60`, because R10 forbids touching
them ("never hardcoded into `agent_core/guardrails.py`, whose defaults and fail policy R6 still
protects").

The consequence contradicts D11/A7:
- the composed stack sets the env, gets 21 s ladders, and clears its 240 s ceiling comfortably;
- **the 180 s ceiling D11 was sized against belongs to the docker-free stack, which sets no
  `GUARDRAILS_*` at all** — so it falls back to the code defaults and keeps 47 s ladders. The
  one stack the arithmetic targets is the one the change does not reach.

Mitigating context, not a resolution: that stack currently cannot reach the gate at all
(`make dev` sets no `GUARDRAILS_URL`), which is the subject of the open task
`2026-08-02-guardrails-dev-stack`. So the 47 s ladder there is presently unreachable — but A7
would be asserted on a number that is not true of that stack today.

This is a requirement conflict (R10 vs A7), not a logic defect, and re-planning is not the
Executor's to do. Both resolutions are the Engineer's:
- (a) permit the two code defaults to move with the declared ones, so a stack that sets nothing
  behaves like a stack that sets everything; or
- (b) narrow A7 to env-declaring stacks and hand the dev stack's values to the sibling task.

Everything else in P6-P10 is complete. Routed to the Validator, which is the sanctioned way to
raise it (`requirement` -> Engineer); PLANNED -> ESCALATED is not a legal transition.

## v3 — PLAN v4, all steps. Supersedes v1/v2 where they conflict.

The image gate from v1 (P1-P5) is unchanged and still stands. v2's budget values are
superseded by the v4 numbers below.

### Changed

| File | Change |
|---|---|
| `mcp/agent_core/guardrails.py` | five ladder defaults -> 15 / 2 / 1 / 1 / 35; module docstring no longer claims exponential backoff; `_timeout`/`_phase_deadline` docstrings carry the reasons |
| `mcp/master_orchestrator/config.py` | `turn_budget_s = 60.0` added; `max_tool_iterations` comment re-grounded; `guardrails_timeout_s` mirror 10 -> 15 |
| `mcp/{doc_analyzer,image_analyzer}/config.py` | same `guardrails_timeout_s` mirror |
| `mcp/master_orchestrator/services/orchestrator.py` | `TurnTimeout` + `TURN_TIMEOUT_CODE`; `run()` bounds `_run_turn()`; `_budget_spent()`; no persist after expiry; `is_retry` marks the stored user message |
| `mcp/master_orchestrator/schemas/http.py` | `OrchestrateRequest.is_retry` |
| `mcp/master_orchestrator/tools/start_job.py` | `TurnTimeout` -> `AgentResponse.fail(..., code=TURN_TIMEOUT_CODE)` |
| `backend/_common/env/settings.py` | `orchestrator_timeout_s` 180 -> 66, comment rewritten |
| `backend/_common/schemas/response.py` | optional `error_code` on `ApiResponse`; `fail()` takes it |
| `backend/gateway/services/agent_client.py` | `AgentOutcome.error_code`; forwarded from envelope `meta.code`; the gateway's own `TimeoutError` sets the same code; `send(..., is_retry)` |
| `backend/gateway/{schemas/chat.py,services/chat_service.py,routers/chat.py}` | `is_retry` through the proxy; 504 + code for the timeout, 502 otherwise |
| `frontend/types/chat.d.ts` | `ChatErrorCode`, `SendMessageRequest.isRetry`, `ChatMessage.retryable` |
| `frontend/services/chatService.ts` | reads `error_code`, `ChatServiceError.code`, sends `is_retry` on both endpoints |
| `frontend/stores/chatStore.ts` | `pending`, `retry()`, timeout branch adds the retry entry instead of an error line |
| `frontend/shared/ui-kit/MessageBubble.tsx`, `.../ChatView.tsx` | the retry button on the retryable entry |
| `docker-compose.yml`, `Makefile`, `.env.example`, `mcp/.env.example` | 15/2/1/1/35, LLM 30, turn 60, gateway 66; `ORCHESTRATOR_SUBAGENT_TIMEOUT_S` deleted; every comment stating an old budget rewritten |
| `mcp/tests/test_gate_budget.py`, `mcp/tests/test_turn_timeout.py` | re-derived / new |

### Deviations from PLAN v4

- **`asyncio.wait_for`, not `asyncio.timeout`.** Same cancellation semantics for a single
  coroutine; `asyncio.timeout` is 3.11+, and the verification interpreter here is 3.10.
  The repo pins >= 3.12, so either would run in production — this one is also testable.
- **`_budget_spent()` is a second guard, not the only one.** D20 relies on cancellation
  reaching the code before `store.save`. Cancellation does arrive first in the normal
  case; the explicit check is what makes the rule hold when the timeout lands during the
  save's own await. Both are cheap, and the failure they prevent (two answers to one
  question in a thread) is not.
- **504, not 502, for the timeout.** The router already maps agent failures to 502; a
  gateway-timeout status is the honest code for the one failure the client is invited to
  retry, and it keeps the branch visible in access logs.

### Verification

- `mcp/tests` -> **31 passed, 2 failed**. Both failures are `test_doc_analyzer_gate.py`
  and pre-date this task: its stub is `_check_input(text, *, source, thread_id=None)`
  (lines 63, 76) while `doc_analyzer` calls it with `surface=`. Neither file is in this
  task's write set. Confirmed unchanged by this step.
- `frontend`: `tsc --noEmit` -> **exit 0**.
- `docker-compose.yml` parses; the mcp service env reads 15 / 2 / 1 / 1 / 35, LLM 30,
  turn 60; backend reads gateway 66.
- A13: `grep -rn ORCHESTRATOR_SUBAGENT_TIMEOUT_S` over compose, Makefile, both
  `.env.example` files and `mcp/` returns nothing.
- A6/R14: `GUARDRAILS_TIMEOUT_S=15`, `RETRY_ATTEMPTS=2`, `RETRY_FACTOR=1`,
  `OUTPUT_DEADLINE_S=35` identical in `agent_core/guardrails.py`, `docker-compose.yml`
  and `mcp/.env.example`.

### Not verified here

- Nothing was run against the pinned interpreter (repo: >= 3.12; sandbox: 3.10) or against
  a live stack. A1 (a real turn aborting at ~66 s), A9 and A10 are behavioural claims that
  need `make up` and a browser; the tests cover the units beneath them, not the wiring.
- `test_doc_analyzer_gate.py`'s two failures are left alone deliberately (A12).

### One observation for the record

`agent_core/guardrails.py` already had `GUARDRAILS_RETRY_ATTEMPTS` defaulting to `2` when
this step opened, though EXEC v2 changed only compose and `mcp/.env.example` and the v2
test run measured a 4-attempt ladder. The file changed outside this task's edits between
the two runs. The end state is what PLAN v4 requires either way, but the discrepancy is
noted rather than assumed away.

## v4 — closes V5 (R18/A14, R25/A15)

### Changed

| File | Change |
|---|---|
| `frontend/stores/chatStore.ts` | `partialize` drops `retryable` entries; the timeout branch now matches on the code duck-typed instead of `instanceof` |
| `frontend/__tests__/chatStore.test.ts` | four cases: the retry offer, the non-timeout path, the re-send, and the non-persistence |
| `mcp/{master_orchestrator,doc_analyzer,image_analyzer}/config.py` | `guardrails_timeout_s` mirrors 10 -> 15 (R25, already applied in v3, now covered by a requirement) |

### V5, and the second defect found while closing it

The persisted retry offer is gone: `partialize` filters `retryable` entries, so a reload
leaves the conversation without the button. The failed turn's own user message is kept —
the user did ask, and hiding the question would be a stranger lie than showing it
unanswered.

While writing the test for it, a defect in v3 surfaced that the type checker cannot see:
the store matched the timeout with `err instanceof ChatServiceError`. The existing suite
mocks `@/services/chatService` with a factory exporting only `sendChatMessage` and
`deleteChatThread`, so inside those tests `ChatServiceError` is `undefined` and
`x instanceof undefined` throws — the error branch of **every** existing store test would
have broken. The check is now duck-typed on `code`, which is also what makes it survive a
second copy of the bundle. Class identity was never the thing the store needed.

### Verification

- `tsc --noEmit` -> exit 0 (with the new tests in the project).
- **The frontend suite could not be run here.** `jest` fails before collection: the Next
  SWC binary in `node_modules` is the host's (darwin), and this sandbox is linux/arm64 —
  `Failed to load SWC binary for linux/arm64`. The four new cases are therefore written but
  unexecuted, and A9/A10/A14 remain unverified by run. This is the same class of gap as the
  macOS venv on the Python side, and it is why the `instanceof` defect above was found by
  reading rather than by a red test.
- `mcp/tests` unchanged by this step: 31 passed, the 2 pre-existing `doc_analyzer` failures.
