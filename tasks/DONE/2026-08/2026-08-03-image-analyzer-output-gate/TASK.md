# TASK — 2026-08-03-image-analyzer-output-gate
owner: Engineer
immutable: true
rewritten: v6 — supersedes the original and every amendment. Earlier text at
`.TASK.v1-v4.superseded`, audit only. Any artifact citing R9-R18, A7 or PLAN D11 cites dead
requirements. One task covers the whole change: the image output gate, the gate's budget, and
the turn ceiling with its retry.

## Context
`image_analyzer` is the only agent that touches an LLM and never calls the gate. Its service
sends prompt + image data-URL to the vision model and returns the answer straight to the tool.
Every other content path is checked on the way in — a prompt at the orchestrator's input gate,
a PDF's text inside `doc_analyzer`, a fetched page at the tool-result gate — but image bytes
are checked by nothing, so the model's answer is the first and only text representation of what
the picture contains.

Adding that gate makes a second output-gate call site in a turn, which is why the gate's budget
and the turn's ceiling are settled here too rather than left to drift.

A turn has no user-facing bound today. The gateway aborts at `orchestrator_timeout_s` — `180.0`
in code, `240` in compose, `180` in the Makefile — and `_call_tool` turns that into
`AgentOutcome(ok=False, error="agent timed out")`, indistinguishable from any other upstream
failure. Nothing bounds the orchestrator's own turn: the loop runs to `max_tool_iterations` and
each sub-agent call is bounded only by `ORCHESTRATOR_SUBAGENT_TIMEOUT_S` (200), which is above
the dev stack's own gateway ceiling. There is no streaming, so the entire wait is a spinner.

## Requirements — the gate call
- R1: `image_analyzer` calls `agent_core.guardrails.check_output` on the model's answer before
  it leaves the agent, `source="image_analyzer"`.
- R2: the call sits in `services/analyze_service.py`, between the LLM call and the returned
  `ImageAnalysis` — not in `tools/` (mcp/CLAUDE.md rule 3).
- R3: on `blocked`, the answer is replaced by one fixed refusal sentence echoing no part of the
  model output, declared beside `DOCUMENT_REJECTED` in `agent_core/guardrails.py`.
- R4: the verdict is binary. On `allowed` the answer is returned unchanged — `verdict.text`,
  `.notice`, `.redactions` do not rewrite it.
- R5: a blocked answer still returns `status=ok`; `AgentResponse.fail` stays reserved for
  failures. `tools/analyze_image.py` is unchanged.
- R6: no local retry, timeout, catch or fallback around the gate call. The fail policy and the
  ladder's structure belong to `agent_core.guardrails`.
- R7: `image_analyzer/config.py` declares the guardrails env contract as `doc_analyzer` does —
  declaration only, never passed into the call.
- R8: no new runtime dependency; no agent imports another.

## Requirements — the gate's budget
- R9: the budget is stated **per call**, never summed across a turn. No requirement or
  acceptance may be derived from adding worst cases: that assumes every gate call hangs at once.
- R10: one attempt is **15 s** (`GUARDRAILS_TIMEOUT_S`) — the gate's judge budget is 8 s and the
  rest is transport and model overhead; tighter turns healthy slow verdicts into false outages.
- R11: **two attempts** (`GUARDRAILS_RETRY_ATTEMPTS`), so one gate call is bounded at ~30 s.
- R12: **no progressive backoff.** `GUARDRAILS_RETRY_FACTOR` is `1`; the gap is flat.
- R13: `GUARDRAILS_OUTPUT_DEADLINE_S` sits above one complete ladder.
- R14: the three declaration sites — defaults in `agent_core/guardrails.py`,
  `docker-compose.yml`, `mcp/.env.example` — agree value for value. A process that sets no
  `GUARDRAILS_*` behaves like one that sets all of them.

## Requirements — the turn ceiling and its retry
- R15: the turn ceiling is **66 s**, the same policy number for the gateway and the mcp
  orchestrator, env-overridable, declared everywhere both stacks read — including
  `.env.example`.
- R16: the orchestrator gets a turn-level bound of its own; today only per-sub-agent and
  per-LLM budgets exist, so the loop can outlive any ceiling the gateway sets. PLAN decides
  whether the orchestrator's effective bound sits strictly below 66 s so the inner layer is the
  one that reports — an outer timeout can only produce a transport error, an inner one can
  produce a message — and states the consequence.
- R17: exceeding the ceiling is a **distinct, typed outcome**, not the generic upstream
  failure. The frontend must tell "ran out of time" from "the agent errored" without
  string-matching `"agent timed out"`.
- R18: on that outcome the UI shows the "Повторите запрос" message with a button, in the
  transcript — not a toast, not a raw error line. The entry is **session-scoped**: it is not
  persisted, so a reload leaves neither the message nor the button. A control that outlives
  the request it would re-send is worse than no control — it is one that does nothing when
  pressed.
- R19: pressing the button re-sends the same request **on the existing `thread_id`**, and the
  resent turn is **marked in thread memory as a retry of the same task** — not recorded as a
  new user request. PLAN chooses the mechanism (a field on the persisted message vs. replacing
  the failed turn's entry) and states what the model sees on rehydration: a retry must not read
  as the user asking twice.
  Ordering fact PLAN must account for: today the turn persists nothing until it succeeds
  (`orchestrator.py:132-134` appends both messages only after the output gate). A turn the
  gateway abandoned at the ceiling may still be running server-side and may persist *after* the
  retry has started, so the marker has to survive a late writer, not just a tidy one.
- R20: `LLM_REQUEST_TIMEOUT_S` becomes **30** (from 90; the root `.env.example` says 45, a
  pre-existing divergence). At 90 with `max_retries=1` a single model call can occupy 180 s,
  which cannot coexist with a 66 s ceiling. `max_retries` itself is not changed.
- R21: `master_orchestrator.max_tool_iterations` is `2` — fewer rounds is what makes a turn fit
  the ceiling.
- R22: every inner budget sits strictly below the one containing it, **per call** — one LLM
  attempt inside one turn, inside the gateway request. It is NOT the sum of the parts: adding a
  30 s vision call to a 31 s gate call is the "everything hangs at once" model R9 rejects, and no
  set of numbers can satisfy it.
- R25: the `guardrails_*` settings mirrors in the sub-agent configs
  (`master_orchestrator`, `doc_analyzer`, `image_analyzer` — `web_agent` has none) declare
  the same env contract and MUST carry the canonical value. They are documentation of the
  env surface, never inputs to the call; a mirror that contradicts what it mirrors is the
  only thing worse than no mirror.
- R24: there is **no per-sub-agent budget level**. `ORCHESTRATOR_SUBAGENT_TIMEOUT_S` is declared
  in `docker-compose.yml`, the `Makefile` and `mcp/.env.example` and read by nothing: no field in
  `master_orchestrator/config.py`, no timeout around `tool.ainvoke` in `orchestrator.py:167`
  (`extra="ignore"` swallows it silently). The turn budget already bounds everything inside it,
  and a second level would only sharpen the error message. Delete the variable at all three
  declaration sites and correct the two comments that cite it as an active bound
  (`docker-compose.yml:131`, `.env.example:40`) — a documented budget that does not exist is
  worse than none, because it is read as protection.
- R23: no streaming, no partial responses, no progress protocol. This bounds the wait and makes
  its end actionable; it does not change the response shape.

## Acceptance
- A1: allowing gate -> the model's answer is returned byte-identical, and the gate saw that
  string with `source="image_analyzer"`.
- A2: blocking gate -> the answer is exactly the R3 constant, holds no substring of the model
  output, envelope status `ok`.
- A3: allowing gate with rewritten `text` and non-empty `redactions` -> the original survives.
- A4: unreachable gate -> the answer is released and the ungated-release incident is logged
  with `source=image_analyzer`; no second error path in the agent.
- A5: with the environment cleared, the ladder from `agent_core`'s defaults equals the one
  declared in `mcp/.env.example`: 15 s per attempt, 2 attempts, flat gap, deadline above the
  total. Asserted by test, re-derived from the values rather than relaxed.
- A6: `TIMEOUT_S=15`, `RETRY_ATTEMPTS=2`, `RETRY_FACTOR=1` and one deadline value, identical
  across the three sites (R14).
- A7: with defaults and no env set, a turn exceeding 66 s is aborted at ~66 s, not 180 or 240;
  and `LLM_REQUEST_TIMEOUT_S` reads 30 at every declaration site.
- A8: the timeout outcome is distinguishable at the gateway's HTTP boundary by a field, not by
  parsing a message (R17).
- A9: the frontend renders the retry message with a working button on that outcome, and behaves
  unchanged on every other failure.
- A10: pressing retry produces a new answer for the same prompt on the same `thread_id`; thread
  memory holds one user message for that task, marked as retried, and the transcript holds no
  orphaned placeholder. A turn that completes server-side after the retry began does not add a
  second copy.
- A11: VALIDATION.md carries a table showing every inner budget strictly below its container
  per call, in both stacks (R22): LLM attempt 30 s < turn 60 s < gateway 66 s. No acceptance is
  computed by summing budgets.
- A13: `grep -rn ORCHESTRATOR_SUBAGENT_TIMEOUT_S` over the repo returns nothing outside task
  artifacts, and no comment describes a per-sub-agent budget (R24).
- A14: after a page reload no entry carries the retry action and no retry button is
  rendered; the transcript keeps the conversation, not the offer to re-send it (R18).
- A15: the `guardrails_timeout_s` mirrors in the three sub-agent configs read the canonical
  value (R25).
- A12: tests covering A1-A5 pass; `test_gate_outage.py` and `test_guardrail_gates.py` still
  pass. `test_doc_analyzer_gate.py` carries two failures predating this task (its stub omits
  `surface`) — out of scope, not to be "fixed" here.

## Constraints
- Frameworks stay pinned; no new runtime dependency; `agent_core.guardrails` mirrors the gate's
  contracts and never imports the `guardrails` distribution.
- The refusal sentence is English, consistent with `REFUSAL_OUTPUT` / `DOCUMENT_REJECTED`.
- PLAN records how the thread id reaches `analyze_service` — the tool signature carries none.
- PLAN chooses `GUARDRAILS_RETRY_BASE_S` and states the trade: `1` makes the ladder 31 s, one
  second over R11's ~30; `0` hits 30 exactly but retries instantly, useless against the
  restarting gate the retry exists for.
- The gateway stays a pure proxy: the ceiling and its outcome are transport concerns; no
  orchestration logic moves into `backend/`.
- `2026-08-02-guardrails-dev-stack` is open and owns the dev stack's guardrails wiring. Where
  this task must touch the same `Makefile` recipes, it touches only its own timeout lines and
  PLAN states the boundary.


## Record correction — Engineer, after VALIDATION v3
VALIDATION v3's issue **V4 was raised against text that no longer exists**. It cited an
acceptance criterion forbidding changes under `backend/` — that criterion belonged to
TASK v5 and was dropped when v6 folded the ceiling and the retry into this task. v6 has no
write-surface criterion at all, so nothing was violated and no exception is needed. The
Validator judged against a superseded version of this file; the finding is withdrawn, not
granted.

What was real in V4 is the second half: the sub-agent config mirrors were edited without a
requirement covering them. R25/A15 now cover them, which is a gap closed rather than an
exception made.
