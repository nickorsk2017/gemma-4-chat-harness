# EXEC — 2026-08-02-injection-reply-backoff

## v1 — Step 0 only (interpreter and base images)

PLAN v2 step 0. Steps 1-9 not started.

### Changed

| File | Change |
|---|---|
| `backend/pyproject.toml` | `requires-python` `>=3.14` → `>=3.12,<3.14` |
| `mcp/pyproject.toml` (dev aggregator) | same |
| `mcp/agent_core/pyproject.toml` | same |
| `mcp/doc_analyzer/pyproject.toml` | same |
| `mcp/image_analyzer/pyproject.toml` | same |
| `mcp/master_orchestrator/pyproject.toml` | same |
| `mcp/web_agent/pyproject.toml` | same |
| `guardrails/pyproject.toml` | unchanged — already `>=3.12,<3.14` |
| `backend/Dockerfile` | `python:3.14-slim` → `python:3.12-slim` |
| `mcp/Dockerfile` | same |
| `guardrails/Dockerfile` | unchanged — already `python:3.12-slim` |
| `frontend/Dockerfile` | unchanged — node, not python |
| `mcp/CLAUDE.md` | stack-conventions language line; states the upper bound and why |
| `backend/CLAUDE.md` | same line, one sentence |
| `Makefile` | `PY_RANGE_CHECK` becomes a range check, not a floor; both operator messages |
| `guardrails/README.md` | the paragraph explaining why it pinned differently — it no longer does |

The `Makefile` change is the one with behaviour, not just wording: `PY_RANGE_CHECK` was
`>= (3,14)` and is now `(3,12) <= v < (3,14)`. Under the old floor a 3.12 interpreter failed
`dev-python`; under a naive edit to `>= (3,12)` a 3.14 interpreter would silently pass and then
fail on the presidio wheel. The bound is checked on both sides for that reason. `dev-install-mcp`
already recreates `mcp/.venv` when its interpreter fails the check, so the existing venv is
replaced rather than reused.

### Not done — verification

**Nothing here has been executed.** The environment this Executor runs in cannot install packages
or build images against the repository: no `pip install`, no `docker build`, no test run. The edits
are textual and were verified by re-reading the files, which is not the same as green.

What must be run before step 1 starts, and what each would catch:

- `make dev-install` — the wheels. This is where a dependency that has already dropped 3.12, or one
  that only ships 3.14 wheels, shows up. PLAN R-8 names this as step 0's failure mode.
- the test suites (`mcp`, `backend`, `guardrails`) — a 3.13/3.14 language feature already in the
  code. Syntax-level ones fail at import; semantic ones may not.
- `docker compose build` — the images, which `TODO.md` records as never having been built even once,
  so a failure here may predate this change rather than follow from it.

Until those pass, step 0 is written, not done. `stage` stays `APPROVED` and `next_actor` stays
`Executor`.

## v2 — Step 4 (review deleted, disclaimer rendered) and A7-1

PLAN v2 step 4, pulled ahead of step 1 at the Engineer's direction: porting the review
router and the store's lifespan onto the MCP surface only to delete both a step later was
work with no destination.

### Deleted

`services/review_store.py` (moved to `_to_delete/`, since this bridge cannot unlink),
the three `/v1/review*` endpoints, `Decision.REVIEW`, `Verdict.review_id`, `ReviewCase`,
`ResolveRequest`, `HELD_FOR_REVIEW`, `GuardrailInfo.held_for_review` / `.review_id`, the
`review_*` settings, the review branches in `Orchestrator.run` (both) and in
`analyze_service`, the `GUARDRAILS_REVIEW_*` compose and `.env.example` entries, the
`sqlalchemy` / `asyncpg` / `aiosqlite` dependencies, the frontend's `heldForReview` /
`reviewId` fields and the "sent to a moderator" line in `MessageBubble`.

The `guardrails` service also loses its `depends_on: postgres` — the store was the only
reason it had one. It no longer holds state.

### Replaced

`MEDICAL_DISCLAIMER` lives in `schemas/verdict.py`, next to `PII_NOTICE_TEMPLATE` and
under the same single-owner rule, and travels in the verdict's existing `notice` field —
no new contract. `_open_review` becomes `_with_disclaimer`, and it **joins** the notices
rather than replacing: when a clinical question also carried a phone number, the user sees
both sentences. A test asserts exactly that, because it is the property an implementation
gets wrong by writing `verdict.notice = DISCLAIMER`.

Both former review paths now resolve to `allowed` — the judge's medical verdict, and the
judge-unavailable case. The second one keeps its old precedence over R8's fail-closed
default: a patient is not refused because the judge is down.

`settings.medical_disclaimer` (env `GUARDRAILS_MEDICAL_DISCLAIMER`) is the toggle; the
constant is not hardcoded in the pipeline.

### A7-1

`REFUSAL_INPUT`, `REFUSAL_OUTPUT` and `MEDICAL_DISCLAIMER` are English.
`DOCUMENT_REJECTED` is added to `agent_core.guardrails` for A5-1's canned sentence, so the
document rejection is spelled once, in the same module as the other two, rather than
inside `doc_analyzer`. Wiring it into `analyze_service` belongs to step 3 — nothing
produces an injection verdict yet.

### Tests

`test_medical_goes_to_review_not_blocked` → `test_medical_is_answered_with_a_disclaimer`;
`..._holds_rather_than_blocks` → `..._answers_rather_than_blocks`;
`test_review_case_carries_no_raw_pii` → `test_the_medical_path_still_redacts_and_keeps_both_notices`;
`test_resolution_records_the_human_decision` deleted with the store;
`test_review_holds_the_turn_without_running_the_loop` →
`test_medical_turn_runs_and_carries_the_disclaimer`, which now asserts the *opposite*
property — the model IS called and the turn IS persisted.

### Verification

`py_compile` passes on all thirteen changed Python files and `docker-compose.yml` parses.
That is syntax, not behaviour: the suites still have to be run here, as with step 0. A
leftover-reference sweep for every deleted symbol comes back empty.

`TODO.md`: the unattended-review-queue entry is deleted (the queue is gone, not fixed) and
replaced by the ungated-image hole recorded under A6-2.

## v3 — Steps 1 and 5 (relocation, MCP transport, retry ladder)

Taken together, not in sequence: step 1 turns the gate into an MCP server and step 5
turns its callers into MCP clients. Landing one without the other leaves the stack
speaking two protocols at once, so there is no green state between them.

### Step 1 — placement and transport

`guardrails/` → `mcp/guardrails/`. `routers/` is replaced by `tools/check.py`: two tools,
`check_input` and `check_output`, each returning `AgentResponse[Verdict]` and catching its
own exceptions, so nothing crosses the MCP boundary as a raise (rule 7). `main.py` becomes
a FastMCP server; `warm_pii()` runs before it binds, not on the first call.

It serves streamable-HTTP on 8200 rather than being spawned over stdio. That is forced by
D9, not chosen: `doc_analyzer` must reach the gate and is itself a subprocess, so it cannot
spawn one.

`HttpServer` is lifted from `master_orchestrator/services/` into `agent_core/http_server.py`
and generalised to `(name, host, port, allowed_hosts)`. Two servers now need the same
DNS-rebinding and Host-header shims, and those shims are version-sensitive: two copies
would drift the first time fastmcp moves. `agent_core` gains no runtime import of
`FastMCP` — it is under `TYPE_CHECKING` — and uvicorn/starlette stay lazy inside `run()`.

The image stays separate, built from context `./mcp` with `dockerfile: guardrails/Dockerfile`
so `agent_core` is reachable. Folding presidio, spaCy and two language models into
`agent-chat/mcp` would make every agent pay for the gate.

**The healthcheck got weaker and it should be said plainly.** `/v1/health` is gone and the
MCP endpoint is a session protocol, not a GET-able page, so the check is now a TCP connect.
It proves the process is listening; it does not prove the gate works.

`mcp/CLAUDE.md` gains rule 1a — the exemption, argued from acyclicity rather than asserted,
plus the statement that a second exception needs the same argument.

### Step 5 — three outcomes and the ladder

`agent_core/guardrails.py` is rewritten as an MCP client. `_post` returning `Verdict | None`
is replaced by `_call` returning a classified `_Result`: **VERDICT**, **RETRYABLE**
(transport, timeout, or an envelope whose `status` is an error), **TERMINAL** (the reply is
not our contract). A6-1's split needed information the old two-valued transport threw away.

`_call_with_ladder` bounds the retry twice — by attempt count *and* by a phase deadline —
because the count alone does not bound wall clock once a per-attempt timeout is in play.
Defaults: 4 attempts, base 1 s, factor 2 (gaps 1/2/4), deadline 60 s, all env-backed (R10).

`check_output` uses the ladder; `check_input` stays single-shot, per the constraint that a
fast refusal must not become a slow one. The fail-open incident now records the attempt
count: an answer released after four tries is a different incident from one released after
none, and the old log could not tell them apart.

### Tests

`test_gate_outage.py` keeps its dead-port approach and gains four cases: input is
single-shot, a decided verdict is not retried, a contract error is not retried, and the
ladder's gaps are 1/2/4 with the deadline winning when the count would have kept going.
The last one uses a stubbed `asyncio.sleep`, so it asserts the schedule without paying it.

### Verification

`py_compile` clean on every changed file; `docker-compose.yml` parses; the four
`requires-python` pins agree; no `httpx`, `/v1/check` or `/v1/health` reference survives in
`agent_core` or `guardrails`. Still syntax, not behaviour — the suites have to run here.

Two things to expect on the first real run, both unverifiable from this side: the exact
shape of `CallToolResult.structured_content` for `AgentResponse[Verdict]`, and whether the
Host shims that were tuned for `mcp:8100` also carry `guardrails:8200`.

## v4 — Steps 2, 3, 7, 8, 9. Execution complete, verification not.

### Steps 2 and 3 — the keyword layer stands down, the model decides

`Category.INJECTION` and a typed `Surface` (prompt / document / tool_result) join the
contract; `Verdict` gains `system_note`. `judge_on_clean` and `lexicon_block_hits` are
gone — there is no deterministic short-circuit left to switch on or threshold.

`scan()` survives, demoted. No branch reads its hits as a decision. Its one remaining job
is aiming `_window` at the passage that matters, which is what stops a 24k-character
document from being truncated blindly from the front. There is exactly one exception and
it is marked as such: in `_no_opinion`, with the model down, its medical signal decides
whether a patient is refused or answered. Nothing else was left to decide it.

`prompts.py` now carries the whole policy in prose, because the model is the whole policy.
The two paragraphs that matter are the ones no word list could express: discussing
injection is not attempting it, and an imperative inside a document *is* an attempt
because a PDF has no standing to instruct anyone. The surface is passed to the model for
exactly that distinction.

**Edits arrive as substrings, not offsets.** The model sees a window; offsets would be
computed against the window and applied to the full text, which silently redacts the wrong
passage on long documents. The gate does the replacing.

`services/fence.py` wraps untrusted text (D17). The nonce makes the marker unguessable,
but what actually holds is `strip_markers`: any marker-shaped string is removed from the
untrusted text before wrapping. A fixed delimiter is closable by any text containing it.

`doc_analyzer` stops concatenating prompt and document. It sent `prompt\\n\\ntext` and
sliced the prompt back off the redacted result by length — arithmetic that breaks the
moment the gate returns text fenced. Only the document is gated now, with
`surface="document"`; the prompt was already checked at the orchestrator. A rejection
yields `DOCUMENT_REJECTED` and no analysis.

### Step 7 — the tool-result gate

`Orchestrator._dispatch` gates a sub-agent's return through `_gate_result`. Which tools
are gated is configuration, not inference: `UNTRUSTED_SUBAGENTS = ["web_agent"]`, carried
to `SubagentToolset.untrusted_tool_names` the same way `file_tool_names` already is.
`doc_analyzer` is deliberately absent per A6-2.

A poisoned result fails the **tool**, not the **turn**, and so does an unreachable gate.
Blocking the turn would let anyone who controls a page in the search results deny service
to any query that reaches it. Single-shot, no ladder: inside the loop a ladder multiplies
the worst case by the iteration count.

### Step 8 — the ceiling

`GATEWAY_ORCHESTRATOR_TIMEOUT_S` 180 → 240, with the arithmetic in a comment beside it.
The four retry knobs and the phase deadline are added to the `mcp` service env.
`ORCHESTRATOR_SUBAGENT_TIMEOUT_S` (200) still sits below the new ceiling and did not move.

### Step 9 — corpora

128 injection cases across 8 attack classes (override, role, exfiltration, fence-escape,
hidden-in-doc, exfil-data, authority, encoded), each in four forms: plain, homoglyph,
zero-width, spaced. 21 benign controls, two of them copied verbatim out of this
repository's own documentation.

**A1 and A2 changed shape, and the Engineer should see this.** They were written for a
deterministic layer, where "every case is caught" is a property. The model decides now, so
what a corpus can measure is a **rate**. `test_injection_corpus.py` runs against the live
model and **skips without a key** rather than passing quietly — a green run that never
called the model would be worse than a red one. Thresholds are 90% recall and 10% false
positives, set deliberately and not pretending to be properties.

### Verification — none of it ran

`py_compile` is clean across every changed file, `docker-compose.yml` parses, the corpus
imports and counts out at 128/21. No suite has been executed: this environment cannot
install packages or reach a model.

What must run before this can be validated:

- `make dev-install` — the pins and wheels (step 0 was confirmed green by the Engineer).
- `pytest` in `mcp/guardrails` and `mcp` — everything above.
- `GEMMA_API_KEY=... pytest tests/test_injection_corpus.py -q -s` — A1/A2, whose numbers
  go in VALIDATION.md.
- `docker compose build && up` — the relocated image, the new build context, and the TCP
  healthcheck that replaced `/v1/health`.

Two things most likely to break first, both unverifiable from here: the shape of
`CallToolResult.structured_content` for `AgentResponse[Verdict]`, and whether the Host
shims tuned for `mcp:8100` also carry `guardrails:8200`.

Not done and not claimed: A8's fresh latency baseline and R-7's concurrency check both
need a running stack. They are the Validator's, not the Executor's.

## v5 — A8-1 applied: the interpreter reverted to 3.14

Eight `requires-python` pins, three Dockerfile bases, the `Makefile` range check (back to a
floor, not a window) and its two operator messages, and the language lines in
`mcp/CLAUDE.md` / `backend/CLAUDE.md`.

The one change that is not a revert: `presidio-analyzer` / `presidio-anonymizer` move from
`>=2.2.355` to `>=2.2.364`. That floor is what makes 3.14 resolvable at all, so it carries
a comment saying why — relaxing it later would reintroduce the failure silently, and by
then nobody would connect a spaCy build error to a presidio floor.

Also fixed here, from the first test runs (VALIDATION V-1, V-2): `dev-install-mcp` now
installs `./mcp/guardrails`, and `make dev` starts the gate as a fourth process, waits on
its port and passes `GUARDRAILS_URL` to the orchestrator. Before this the docker-free stack
had no gate at all and, being fail-closed on input, refused every prompt.

Unverified as always from here: `make dev-install` on 3.14 is exactly the thing this
amendment claims works, and it is the Engineer's next command.

## v6 — A9-1 applied: no ML stack in the gate

`detectors/pii.py` rewritten without presidio. Added: Luhn, IBAN mod-97, an email pattern —
the three things presidio's built-ins were supplying. Kept unchanged: the SNILS, INN and
passport checksum validators, the overlap resolution, and the right-to-left replacement,
all of which were already this file's own. `mask_spans` is factored out so the model path
and the deterministic path share one replacement routine.

`warmup()` survives as the startup hook but is now trivial. It used to build presidio's
analyzer, which took tens of seconds — longer than the callers' timeout, so the first
request after every deploy tripped the fail-closed path. That failure mode is gone.

Removed from the image: presidio-analyzer, presidio-anonymizer, spacy, and everything they
dragged in (thinc, blis, numpy, srsly, preshed, cymem, murmurhash, tldextract, phonenumbers,
click, pyyaml, regex), plus both `spacy download` steps. `pyahocorasick` is the only
compiled dependency left.

Model side: `JudgeVerdict.pii`, a `pii` block in the prompt with an explicit instruction
*not* to list formatted types (they are already `<PLACEHOLDER>` by the time it sees the
text), and `_mask_model_pii` in the pipeline. The notice is **rebuilt** rather than appended
to, because the deterministic pass has already written one by then and the R5 string must
name every type removed.

`GUARDRAILS_PII_USE_NLP` is gone; `GUARDRAILS_PII_MODEL_ENTITIES` replaces it.

Verified here: `py_compile` clean, and the two new validators smoke-tested against known
vectors (4111 1111 1111 1111 passes Luhn and 4111…1112 fails; DE89 3704 0044 0532 0130 00
and GB82 WEST 1234 5698 7654 32 pass mod-97, a one-digit mutation fails). `test_pii.py`
is unchanged and is the real acceptance — it asserts behaviour, not presidio.
