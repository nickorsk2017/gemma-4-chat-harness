# PLAN — 2026-08-03-image-analyzer-output-gate

## v1

### Decisions

**D1 — The output gate belongs to `image_analyzer` because the image never passes a gate at
all.** Every other content path into the system is checked on the way in: a prompt at the
orchestrator's input gate, a PDF's extracted text inside `doc_analyzer`, a fetched page at the
tool-result gate. Image bytes are checked by nothing — they are handed to the vision model as a
data-URL, and the model's answer is the *first and only* text representation of what the image
contains. That makes this call site categorically different from the other three: it is not a
second opinion on already-checked text, it is the sole enforcement point for a whole input
modality. This is the argument R1 rests on, and it is the reason the exclusion recorded for
`doc_analyzer` in `UNTRUSTED_SUBAGENTS` ("its document is already checked on the way in") does
not transfer to images.

**D1a — Rejected: adding `image_analyzer` to `UNTRUSTED_SUBAGENTS` instead.** It is the cheaper
change (one config list, no agent code) and it was considered first. It fails on three counts,
any one of which is decisive:
- that path calls `check_input` with `surface="tool_result"` — an inbound/injection judgement.
  The question here is whether *our own answer* is fit to leave, which is what the output
  direction and its category set exist for.
- its blocked branch discards the result and returns `ok=False` — deliberately so. R3/R5 require
  a refusal sentence carried in a successful envelope.
- it is fail-closed-drop on an unreachable gate, where R6 requires the inherited fail-open.
Plus it is a `master_orchestrator` edit, which A6 forbids.

**D2 — The gate sits after the answer is flattened to `str`, not around the LLM call.** The
gate's contract is text; `reply.content` may be a string or a block list, and the existing flatten
step is what produces the value that becomes `ImageAnalysis.answer`. Gating the flattened value is
what makes "what was gated" and "what is returned" the same object rather than two derivations of
one source. Same placement principle as `doc_analyzer` (the service owns the LLM boundary, R2),
opposite side of the call.

**D3 — Blocked is a return, not a raise — the `doc_analyzer` idiom must NOT be copied.**
`doc_analyzer` raises `DocumentBlocked`, and its tool's blanket `except` turns that into
`AgentResponse.fail`; a blocked document is therefore an *error* envelope today. R5 requires the
opposite for images: a verdict is not a failure. So no new exception type, no `tools/` change —
the service returns a normal `ImageAnalysis` whose `answer` is the refusal constant, and the
existing `AgentResponse.ok` path carries it unchanged. The divergence from the sibling agent is
intentional and is the single most likely thing for the Executor to get wrong by analogy.

**D4 — Binary verdict: on `allowed`, nothing is read off the verdict but the decision.** R4
forbids substituting `verdict.text`. The reason it is safe to ignore here, where `doc_analyzer`
must not ignore it, is direction: on the input path the gate's text is a *fence* around untrusted
content and dropping it would send unfenced text to the model. On the output path the text is a
redaction of our own answer, and this task's scope decision is block-only. `notice`,
`system_note` and `redactions` are likewise unread. `known_pii_types` is passed empty — the value
the orchestrator passes there comes from its own input verdict, which this agent never sees.

**D5 — `thread_id=None`, and that is a decision, not an omission** (TASK constraint). The tool
signature is `(prompt, file)`; a thread id is not model-supplied data, so it cannot be added as a
tool parameter without inviting the model to invent one. The one mechanism that injects
non-model data into a sub-agent call is the orchestrator's file injection at dispatch, and
extending it is a `master_orchestrator` change that A6 forbids. Consequence to accept: this
agent's gate incidents are correlatable by `source="image_analyzer"` but not by thread. Threading
a request context through sub-agent dispatch is a separate task with its own blast radius.

**D6 — No new field on `ImageAnalysis`, no `meta` on the envelope.** Reporting *that* an answer
was blocked is desirable, but a schema change reclassifies this task as HIGH (SETTINGS.md
classification rules) for observability that `agent_core.guardrails` already partly provides. A
single service-level log line at `warning` covers the operational need within MEDIUM. If a
structured `GuardrailInfo` for sub-agents is wanted, it is its own task.

**D7 — The config fields (R7) declare the env contract; they do not feed the call.**
`agent_core.guardrails` reads `GUARDRAILS_URL` / `GUARDRAILS_TIMEOUT_S` from `os.environ` at call
time by design (one policy owner, R6). The settings mirror in `doc_analyzer/config.py` exists so
the agent's env surface is discoverable and validated, not so it can be passed in. Copy that
shape exactly; wiring the settings object into the call would create a second source of truth for
a policy value.

### Impact map

| File | Change | Req |
|------|--------|-----|
| `mcp/agent_core/guardrails.py` | one added refusal constant, next to `DOCUMENT_REJECTED` | R3 |
| `mcp/image_analyzer/services/analyze_service.py` | gate call + block branch + rationale docstring | R1, R2, R4, D3 |
| `mcp/image_analyzer/config.py` | two settings fields mirroring `doc_analyzer/config.py` | R7 |
| `mcp/tests/test_image_analyzer_gate.py` | new suite, A1–A4 | A5 |
| `mcp/image_analyzer/tools/analyze_image.py` | **unchanged** — D3 keeps the envelope path as-is | R5, A6 |

No file under `doc_analyzer/`, `web_agent/`, `master_orchestrator/` is touched (A6).

### Steps

1. Add the refusal constant to `agent_core/guardrails.py`. Wording follows the
   `DOCUMENT_REJECTED` register: states the answer was withheld, names no category detail it
   cannot know (the output gate returns categories, but echoing them back is not required by R3
   and widens the copy surface), echoes nothing of the answer.
2. Add the two guardrails fields to `image_analyzer/config.py` per D7 — same defaults, same
   `validation_alias` values as `doc_analyzer/config.py`.
3. Gate in `analyze_service.py` per D2/D3/D4: flatten, gate, branch, construct `ImageAnalysis`.
   One `warning` log on the blocked branch (D6). No try/except around the gate call (R6 — the
   ladder and the fail-open verdict are the gate client's; catching here would add a second
   policy owner).
4. New test module `mcp/tests/test_image_analyzer_gate.py`, four cases mapping 1:1 to A1–A4.
   Stub the model the way `test_doc_analyzer_gate.py` does (monkeypatch `get_llm` on the service
   module). Stub the gate at the name the service resolves at call time, not at
   `agent_core.guardrails` — patching the definition site while the service holds a from-import
   silently tests nothing (see R-4).
   - A2 asserts the exact constant AND that the model's distinctive answer text is absent.
   - A3 hands back an `allowed` verdict whose `text` differs from the answer and whose
     `redactions` are non-empty; the assertion is that the original survives.
   - A4 drives the real `check_output` with an unreachable base URL so the ladder's own
     fail-open produces the verdict — a stub returning fail-open would test the stub. Keep the
     attempt count and backoff env-clamped to 1 / 0s in that test so it stays fast.
5. Run the three existing gate suites plus the new one (A5), then `git diff --name-only` for A6.

### Risks

- **R-1 (latency, the one worth arguing about).** `check_output` carries the R6 ladder:
  4 attempts, exponential backoff, 60s phase deadline. A turn that analyses an image now crosses
  the ladder twice in series — once inside the sub-agent, once at the merge — so a gate outage
  can add up to 2 x `GUARDRAILS_OUTPUT_DEADLINE_S` before an answer is released, against a single
  gateway request timeout. The Executor must not "fix" this locally (R6). The correct lever is
  the existing env knobs, which is why R7's config surface matters; the Validator should check
  the arithmetic against the gateway timeout and raise it as an issue if the worst case exceeds
  it, rather than treating it as noise.
- **R-2 (the analogy trap).** `doc_analyzer` is the nearest neighbour and it raises. D3 says do
  not. Highest-probability defect in this task.
- **R-3.** Assigning `verdict.text` on the allowed branch "because that is what the orchestrator
  does" — violates R4. The orchestrator is the redaction point; this agent is not.
- **R-4 (a test that passes while enforcing nothing).** If the service from-imports the gate
  function, monkeypatching `agent_core.guardrails.check_output` leaves the service's own
  reference untouched and every case still passes. Whichever import form step 3 chooses, step 4's
  stub must target the same name.
- **R-5 (scope creep into the input side).** The image itself remains ungated; that is the
  Engineer's scope decision, not an oversight. Any "while we are here" input-side check is
  out of scope and is a Planner-routed change if wanted.

## v2 — closes V1 (TASK amendment v2: R9-R11, A7-A8)

v1 stands. Steps P1-P5 are unaffected; P6-P9 are added and PLAN R-1 is superseded by D11.

### Decisions

**D8 — The binding ceiling is 180 s, and it is the dev stack's, not the composed stack's.**
`GATEWAY_ORCHESTRATOR_TIMEOUT_S` is `240` in `docker-compose.yml` (raised deliberately by an
earlier task, with its arithmetic recorded in the file) but `180` in the `Makefile`'s
docker-free stack (two places: the `dev` and `run-*` recipes). `backend/_common/env/settings.py`
defaults to `180.0`. A7 names 180.0, so all arithmetic below is against 180 and the composed
stack inherits the margin for free.

Noted, not fixed here: in the dev stack `ORCHESTRATOR_SUBAGENT_TIMEOUT_S=200` sits *above* its
own gateway ceiling of 180, which inverts the invariant compose states explicitly ("keep below
the gateway's..."). That is dev-stack wiring — the write surface of the open task
`2026-08-02-guardrails-dev-stack` — and this task must not reach into it (see D12).

**D9 — `GUARDRAILS_TIMEOUT_S` is not a lever. Its floor is set by the gate's own judge.**
`guardrails.config.judge_timeout_s = 8.0`, and compose comments already record that the judge
gets its own budget. A per-attempt client timeout of 10 s is 8 s + 2 s of margin — that is why
the value is 10 and not a round number. Cutting it to 5 s to buy headroom would time out
*healthy* gate calls whose judge is merely thinking, and the consequences are asymmetric and
bad on both paths: on output a manufactured outage releases the answer ungated (fail-open), on
input it refuses a legitimate prompt (fail-closed). Buying seconds by converting working
verdicts into fake outages defeats the point of the gate. `GUARDRAILS_TIMEOUT_S`,
`GUARDRAILS_RETRY_BASE_S` and `GUARDRAILS_RETRY_FACTOR` therefore stay unchanged.

**D10 — The levers are the attempt count and the phase deadline.** `GUARDRAILS_RETRY_ATTEMPTS`
4 -> 2 and `GUARDRAILS_OUTPUT_DEADLINE_S` 60 -> 22. One output ladder against a dead gate
becomes 10 + 1 + 10 = **21 s** (was 4 x 10 + 1 + 2 + 4 = 47 s); the deadline stays just above it
so it remains a guard rather than the binding constraint. The ladder still exists — R6's policy
is untouched, only its budget moves, which is exactly what R10 authorises.

Consequence to accept: the knobs are process-global, so the merge gate gets the shortened
ladder too. That is not a side effect to apologise for — it is the same trade at both call
sites, and the merge gate's 47 s was itself sized when it was the only ladder in the turn.

**D11 — R11 arithmetic. Supersedes PLAN v1 R-1.**

The expensive scenario is *not* a total outage: `check_input` is single-shot and fail-closed, so
a gate that is down before the turn starts ends it in ~10 s. The worst case is an outage that
begins *after* the input check passes — a restart, a rolling deploy, an overloaded gate.

Gate-attributable time, outage after input, `max_tool_iterations = 2` (R9):

| Segment | Cost |
|---|---|
| input gate (single-shot, succeeded) | 10 s |
| round 1 image tool -> output ladder | 21 s |
| round 2 image tool -> output ladder | 21 s |
| merge gate -> output ladder | 21 s |
| **gate total** | **73 s** |

Same table before this task: 10 + 47 = 57 s. After: 73 s (+16 s), against the 47 s single-ladder
figure the composed stack's ceiling was originally sized around.

Healthy-but-slow gate (every check hits the 8 s judge timeout): 8 x 4 = **32 s**.

Leaves 180 - 73 = **107 s** for all model work in the worst gate case: two vision calls plus up
to three orchestrator rounds. At nominal latency that is comfortable.

**Stated plainly, because R11 says count the LLM calls rather than ignore them:** one *hung*
LLM attempt is 90 s (`LLM_REQUEST_TIMEOUT_S`) and `agent_core.llm` sets `max_retries=1`, so a
single hung call can consume 180 s on its own and breach the ceiling with zero gate time
involved. That exposure predates this task, is unchanged by it, and is not closable within R9 +
R10 — the fix is a retry/timeout question for `agent_core.llm` and the two stacks' ceilings.
**It is flagged here for its own task and must not be absorbed into this one.** A7 is met on the
bound this task controls: gate-attributable time, 73 s worst case, and no path this task adds
can exceed it.

**D12 — Declaration surface (A8): compose + `mcp/.env.example` only.** Both new values go where
the ladder is already declared (`docker-compose.yml`, mcp service env) and into
`mcp/.env.example`, which today documents only `GUARDRAILS_URL` and `GUARDRAILS_TIMEOUT_S` —
the ladder vars are missing there, so a native run silently gets the code defaults. Adding all
four closes that.

The root `.env.example` and the `Makefile` dev stack are **deliberately not touched**: R4 of the
open task `2026-08-02-guardrails-dev-stack` owns exactly those files for exactly these
variables. Two open tasks editing the same recipes is how a conflict ships. This task's values
land in the shared files; that task picks them up when it wires the dev stack.

### Steps (added)

6. `master_orchestrator/config.py`: `max_tool_iterations` default 4 -> 2 (R9). The comment above
   it states the loop bound, and must now also state why the number is what it is — it is a
   guardrails budget input, not just a model-behaviour knob.
7. `docker-compose.yml`, mcp service env: `GUARDRAILS_RETRY_ATTEMPTS` default 4 -> 2,
   `GUARDRAILS_OUTPUT_DEADLINE_S` 60 -> 22. Both keep their `${VAR:-default}` form.
8. Same two values added to `mcp/.env.example`'s guardrails block, alongside
   `GUARDRAILS_RETRY_BASE_S` and `GUARDRAILS_RETRY_FACTOR` which are also missing there (D12).
9. The compose comment above the ladder vars currently reads "Four attempts with 1/2/4s between
   them is 47s worst case" — after step 7 that sentence is false. Replace it with D10/D11's
   numbers, including why `GUARDRAILS_TIMEOUT_S` stays at 10 (D9). A stale comment next to a
   safety budget is worse than none.
10. Test: assert `OrchestratorSettings().max_tool_iterations == 2`. Cheap, and it is the value
   D11's arithmetic depends on — a later bump back to 4 silently invalidates A7.

### Risks (added)

- **R-6 (the one that matters).** Fewer attempts means a *transient* gate blip that four
  attempts would have ridden out now falls through to fail-open, releasing an answer ungated.
  This is a real reduction in enforcement bought for latency, it is the Engineer's call, and it
  should be recorded as such rather than presented as a free win. The 1 s gap still covers a
  process restart; it no longer covers a multi-second one.
- **R-7.** D11's 107 s LLM headroom assumes nominal model latency. The hung-call path is
  documented, not defended.
- **R-8.** Step 9 is the sort of edit that gets skipped as cosmetic. The comment is the only
  place the ladder's cost is written down for an operator reading compose.

## v3 — re-cut against TASK v6 (supersedes v2 entirely)

**Withdrawn: D8, D9(partially), D10, D11, D12 and risks R-1/R-6.** They encoded the summed-turn
accounting TASK R9 forbids. D11's turn table is deleted, not updated: it added up worst cases on
the assumption that every gate call in a turn hangs at once, and the budget is now stated per
call with the ceiling and the retry doing the work that arithmetic was doing badly.

**Still standing from v1:** D1, D1a, D2, D3, D4, D5, D6, D7 and risks R-2..R-5 — the gate call
itself is unchanged by any amendment. D9's *reason* survives its number (see D13).

### Decisions — the gate's budget (R9-R14)

**D13 — 15 s per attempt has a floor, not a preference.** `guardrails.config.judge_timeout_s`
is 8 s. The client budget must cover the judge plus transport, model handshake and scheduling;
at 10 s the margin was 2 s, which is thin enough that a healthy-but-thinking gate reads as an
outage. That failure is asymmetric and bad on both paths — output releases ungated (fail-open),
input refuses a legitimate prompt (fail-closed). 15 s is 8 + 7.

**D14 — the gap stays at 1 s, and the ladder is 31 s, not 30.** `GUARDRAILS_RETRY_BASE_S = 1`,
`GUARDRAILS_RETRY_FACTOR = 1` (flat, R12). A zero gap would hit the round 30 s exactly and make
the retry worthless for the case it exists for: a gate that is restarting refuses instantly, and
an instant second attempt hits the same closed socket. One second is the cheapest gap that can
observe a state change. The one-second overshoot of "~30 s" is the price of the retry meaning
anything.

**D15 — deadline 35 s.** R13 requires it above one complete ladder (31 s). 32 would satisfy the
letter and trip on scheduling jitter, cutting the second attempt short — the exact failure the
deadline exists to prevent. 35 gives 4 s of slack and still bounds the phase well under any
container (D17).

**D16 — the code defaults become the declared values (R14).** `agent_core/guardrails.py`'s
`os.environ.get(..., "<default>")` literals move to 15 / 2 / 1 / 1 / 35, matching
`mcp/.env.example` and compose. This is what closes the hole EXEC v2 found: the docker-free
stack sets no `GUARDRAILS_*` at all, so it runs on these literals — a stack that declares
nothing must behave like one that declares everything. Only the five literals change; the fail
policy, the classification and the ladder's structure stay untouched (R6).

### Decisions — the ceiling and the retry (R15-R23)

**D17 — the budget ladder, each level strictly inside the one above it (R22).**

| Level | Value | Why it sits there |
|---|---|---|
| one LLM attempt | 30 s (`LLM_REQUEST_TIMEOUT_S`, R20) | 90 was sized for batch document work, not a turn |
| one gate call | 31 s (D14) | two attempts + gap |
| one sub-agent call | **50 s** (`ORCHESTRATOR_SUBAGENT_TIMEOUT_S`, was 200) | must contain a vision call plus its output gate, and still fit the turn |
| orchestrator turn | **60 s** (new, D18) | reports *before* the gateway gives up |
| gateway request | **66 s** (`GATEWAY_ORCHESTRATOR_TIMEOUT_S`, R15) | outermost backstop |

`max_retries=1` on the model means one LLM call can take 2 x 30 = 60 s; the 50 s sub-agent
budget cuts it first, which is the containment working as intended rather than a contradiction.
200 -> 50 is the change that makes R22 true: today the sub-agent budget exceeds the dev stack's
whole ceiling.

**D18 — the orchestrator gets a turn budget of its own, and it is what produces the message.**
`asyncio.timeout(60)` wraps the orchestration turn inside `master_orchestrator`. The layering is
the point (R16): the *outer* gateway timeout can only ever produce a transport error, because by
the time it fires there is no agent response to shape. An *inner* bound still holds a live code
path, so it can return a well-formed envelope carrying a machine-readable reason. 60 < 66 makes
the inner one always first; the gateway's 66 s remains as the backstop for a process that is
wedged below the asyncio level.

**D19 — the typed outcome is a code on the existing envelopes, not a new shape (R17).** The
chain is `AgentResponse.meta["code"] = "turn_timeout"` -> `AgentOutcome` carries it ->
`ApiResponse` grows an optional `error_code` beside `error_text`. The frontend branches on
`error_code === "turn_timeout"`, never on message text. Two paths must set the same code: the
orchestrator's own 60 s bound (D18) and the gateway's 66 s backstop, or the backstop degrades
the UI to a generic failure exactly when the system is worst off. `ApiResponse` is shared by
every router, so the field is optional and additive — no existing response changes shape.

**D20 — a turn that lost its budget writes nothing.** The late-writer problem R19 names is real
but narrow: the orchestrator persists both messages only after the output gate
(`orchestrator.py:132-134`), so an abandoned turn normally leaves no trace — unless it finishes
just after the retry started and appends to the same thread. The fix is not a marker but an
ordering rule: on timeout the turn is cancelled at the `asyncio.timeout` boundary, before the
persist, and any turn whose budget has expired must not save. Cancellation gives this for free
provided nothing swallows `CancelledError` around the save.

**D21 — the retry marker is on the retry, not on the corpse.** Since the failed turn persists
nothing (D20), there is no entry to mark. The retry carries `is_retry` on the chat request,
reuses the `thread_id`, and the orchestrator persists its user message as
`{"role": "user", "text": ..., "retry": true}`. `_rehydrate` reads only `role` and `text`, so
the extra key is inert on the model-facing path — which is the requirement: a retry must not
read to the model as the user asking twice. The flag exists for the transcript and for
debugging a thread after the fact, and it survives a late writer because a late writer no longer
writes (D20).

**D22 — the frontend keeps the failed turn's request, not just its error.** `chatStore` holds
`error` as a string today. It gains the pending request (prompt + file + thread_id) alongside
`error_code`, so the button has something to re-send. The retry message renders in the
transcript as an assistant-side entry with an action, not a toast; on success it is replaced by
the answer, so no orphaned placeholder survives (A10).

### Steps

1. `agent_core/guardrails.py`: five default literals -> 15 / 2 / 1 / 1 / 35 (D16). Nothing else.
2. `docker-compose.yml` + `mcp/.env.example`: same five values; correct the ladder comment,
   which still describes the old attempt count and cost.
3. `master_orchestrator/config.py`: `max_tool_iterations = 2` (already done in EXEC v2, keep),
   add the turn budget setting (default 60, env-overridable).
4. `master_orchestrator`: wrap the turn in `asyncio.timeout` (D18); on expiry return the
   envelope carrying `code="turn_timeout"`; ensure the persist cannot run after expiry (D20).
5. `backend/_common/env/settings.py`: `orchestrator_timeout_s` default 180 -> 66. Compose,
   Makefile, `.env.example`, `mcp/.env.example`: 66 for the gateway, 50 for the sub-agent
   budget, 30 for `LLM_REQUEST_TIMEOUT_S` (the root `.env.example`'s stray 45 included).
6. `backend/_common/schemas/response.py`: optional `error_code` on `ApiResponse`;
   `agent_client` / `chat.py` router propagate it, and the gateway's own `TimeoutError` branch
   sets the same code (D19).
7. `frontend`: `types/chat.d.ts` gains `error_code` and the retry request shape; `chatStore`
   keeps the pending request; `ChatView`/`MessageBubble` render the retry entry with its button;
   the resend sends `is_retry` on the same `thread_id`.
8. Tests: the gate suite and `test_gate_budget.py` re-derived from D14/D15/D16 (A5, A6); a turn
   that exceeds the orchestrator budget returns `turn_timeout` and persists nothing (A7, A8,
   A10); the budget ordering table asserted as a test, not only in prose (A11).

### Risks

- **R-9.** Two attempts instead of four means a transient blip that the old ladder rode out now
  falls through to fail-open. Real reduction in enforcement, bought deliberately for latency.
- **R-10.** `ORCHESTRATOR_SUBAGENT_TIMEOUT_S` 200 -> 50 is the largest behavioural change in the
  set: a genuinely slow document or image turn that used to finish now fails and shows the retry.
  That is the intent, but it will read as a regression to anyone who has not seen this task.
- **R-11.** D20 depends on cancellation propagating. A broad `except Exception` around the save
  path would swallow `CancelledError` on older idioms; the Executor must check what sits between
  the timeout boundary and `store.save`.
- **R-12.** `ApiResponse` is shared by every router. The new field must be optional and must not
  alter existing serialised responses; the delete/health endpoints are the canaries.
- **R-13.** The retry button re-sends on the same `thread_id`. If the abandoned turn's
  cancellation is not clean, two orchestrations can run against one thread concurrently; the
  checkpointer is last-write-wins.

## v4 — patch of v3 for R22 (per-call reading) and R24 (no sub-agent level)

Only D17 and steps 3/5 change. Everything else in v3 stands.

**D17 (revised) — three levels, not four.**

| Level | Value | Why it sits there |
|---|---|---|
| one LLM attempt | 30 s (`LLM_REQUEST_TIMEOUT_S`, R20) | 90 was sized for batch document work |
| one gate call | 31 s (D14) | two attempts + flat gap; a peer of the LLM attempt, not a container |
| orchestrator turn | 60 s (D18) | reports before the gateway gives up |
| gateway request | 66 s (R15) | outermost backstop |

Containment is read **per call** (R22): one LLM attempt or one gate call sits inside one turn,
which sits inside the gateway request. The parts are not added. The v3 row for a 50 s
per-sub-agent budget is withdrawn — it described a level that does not exist.

**D23 — the sub-agent budget was never a budget.** `ORCHESTRATOR_SUBAGENT_TIMEOUT_S` is declared
in `docker-compose.yml:71`, `Makefile:188` and `mcp/.env.example:8`, and read by nothing:
`master_orchestrator/config.py` declares no such field and `extra="ignore"` swallows it, while
`orchestrator.py:167` wraps `tool.ainvoke` in no timeout at all. Two comments
(`docker-compose.yml:131`, `.env.example:40`) cite it as an active bound, which is how it
survived — the documentation was the only place it existed.

Given the turn budget (D18) already bounds everything a turn can do, introducing the missing
mechanism would buy one thing: a more precise failure ("this sub-agent ran out" instead of "the
turn ran out"). That is not worth a second cancellation boundary around a `gather` whose
interaction with D20's no-write-after-expiry rule would have to be reasoned about separately.
The level is dropped and the variable deleted (R24). If per-sub-agent attribution is wanted
later, it is a task with a clear question rather than a leftover.

**Consequence worth stating:** a single sub-agent can now consume the whole 60 s turn. That was
already true today — nothing bounded it — so this is a documentation change, not a behavioural
one. What changes is that the failure is now visible (typed timeout + retry) instead of a
180-240 s wait ending in a generic error.

### Steps (patched)

3 (revised). `master_orchestrator/config.py`: keep `max_tool_iterations = 2`; add the turn
budget field (default 60, env-overridable). No sub-agent timeout field is added.

5 (revised). `backend/_common/env/settings.py`: `orchestrator_timeout_s` 180 -> 66. Compose,
`Makefile`, `.env.example`, `mcp/.env.example`: gateway 66 and `LLM_REQUEST_TIMEOUT_S` 30 (the
root file's stray 45 included). **Delete** `ORCHESTRATOR_SUBAGENT_TIMEOUT_S` from
`docker-compose.yml:71`, `Makefile:188`, `mcp/.env.example:8`, and rewrite the two comments that
describe it as a bound (`docker-compose.yml:131`, `.env.example:40`) so no reader infers a
protection that never existed.

8 (extended). Add the A13 check to the suite or to VALIDATION's evidence: a repo grep for the
deleted variable returns nothing outside task artifacts.

### Risks (patched)

- **R-10 (revised).** The v3 risk (200 -> 50 cutting slow sub-agents) is withdrawn: there was no
  cut to make. The live risk is the opposite one — a slow sub-agent now consumes the turn budget
  and the user sees the retry affordance rather than a longer wait. Intended, but it is the
  behaviour change most likely to be reported as a regression.
