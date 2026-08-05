# PLAN — 2026-08-02-guardrails-service

## v1

### Decisions

**D1 — Placement: new top-level `guardrails/` service.** Not under `mcp/`, not under `backend/`.
`mcp/` is a star topology: sub-agents are reached only by `master_orchestrator` and no agent may
import another (`mcp/CLAUDE.md` rule + Agents table). R6b requires `doc_analyzer` to call the gate,
which a sub-agent peer cannot legally be. `backend/` pins Python >= 3.14, which the constraint on
ML/NLP wheels rules out for this service. A neutral top-level distribution with its own container
and its own interpreter pin satisfies R1 and both constraints without amending either subsystem's
rules. Rejected alternative: `backend/guardrails/` as a second bounded context — reuses `_common`
and the ApiResponse envelope, but inherits the 3.14 pin and makes an `mcp/` agent an HTTP client of
`backend/`, which inverts the current dependency direction.

**D2 — Transport: HTTP/JSON, two endpoints,** mirroring R2 one-to-one. Callers hold a thin local
client and a mirrored contract module; no cross-subsystem package import. Precedent exists —
`gateway.schemas.chat.FilePayload` already mirrors `agent_core.files.FilePayload` field-for-field
rather than importing it (`backend/CLAUDE.md` rule 7).

**D3 — Cascade, cheapest layer first.** Input: normalize -> deterministic PII -> lexicon topic
match -> LLM judge, invoked only when the deterministic layers are inconclusive. Output: topic judge
+ PII leak scan against the types redacted on the way in. The judge is the only layer with unbounded
latency, so it must be the layer that is skipped most often; the fast-path/judge invocation ratio is
the metric A4 measures.

**D4 — Detection stack.** PII: Presidio with custom RU recognizers (passport, SNILS, INN) carrying
checksum validators, not bare regex — R4 types not covered by Presidio built-ins. Topic fast path:
curated RU+EN lexicon over an Aho-Corasick automaton, applied post-normalization (R9). Judge: the
existing Novita gemma provider with a structured verdict contract. No local classifier model in v1 —
it is a provider swap behind D2's contract if A4 or cost forces it, and that swap must not change
the API.

**D5 — Gateway enforcement vs. the pure-proxy rule.** `backend/gateway` is documented as holding no
logic and deciding nothing (`routers/chat.py`, `services/chat_service.py`, `backend/CLAUDE.md`
rule 2). R6a and R6c place two enforcement points there. Resolution: the gateway *delegates* the
decision — it calls the gate and forwards the verdict, computing no policy itself, which preserves
the rule's intent (no logic in the gateway) while satisfying R6. The call belongs in `services/`,
never in `routers/` (rule 2). This is the decision that most needs the HIGH approval gate; if the
Engineer rejects it, the fallback is enforcement at the `master_orchestrator` entry, which keeps the
gateway untouched but loses fail-closed *before* the network hop into `mcp/` and leaves the REST
surface unguarded.

**D6 — Output choke point: gateway response path.** Both `/api/chat` and `/api/chat/files` converge
on `ChatService` and one `AgentOutcome`; gating there covers R6c once instead of per-route.

**D7 — `doc_analyzer` insertion point.** Between text extraction and the LLM call inside
`services/analyze_service.py`, not in `tools/doc_tools.py` — tools stay thin (`mcp/CLAUDE.md`
rule 3), and A3 asserts at the LLM boundary, which only the service layer owns.

**D8 — The R5 notice is produced by the service, not the callers.** The verdict carries
`redacted_text` and the rendered notice; each caller substitutes and appends. One owner of the
string, three call sites, no drift — and A2 can assert it once.

### Impact map

| Area | Change |
|---|---|
| `guardrails/` (new) | service, contracts, detectors, providers, config, container |
| `backend/gateway/services/chat_service.py` | input gate before forward, output gate after (D5, D6) |
| `backend/gateway/schemas/chat.py` | carry the R5 flag/notice outward (constraint: extend, not break) |
| `backend/_common/env` | guardrails URL, timeouts, fail-mode (R10) |
| `mcp/doc_analyzer/services/analyze_service.py` | gate between extraction and LLM (D7) |
| `mcp/doc_analyzer/config.py` | guardrails endpoint + timeout (R10) |
| `docker-compose.yml` | new service, network, healthcheck, deps from backend and mcp |
| `frontend/` | surface the R5 notice (constraint) |
| tests/fixtures | A1 corpus, A2 PII set, A3 integration, A5 outage |

### Risks

- **R-1 Judge latency.** `agent_core.llm` defaults to a 90s per-attempt timeout with one retry. The
  gate must impose its own far shorter budget; inheriting the agent budget would make R8's
  fail-closed path indistinguishable from a hang. A4's p95 depends on this being explicit.
- **R-2 Document volume.** R6b feeds full extracted PDF text through the gate. Judging the whole
  document per request is the dominant cost in the system; the plan must bound what the judge sees
  (segment selection driven by the deterministic layers) rather than passing everything.
- **R-3 False positives on benign pharmacology/medicine.** A1 makes this measurable but sets no
  ceiling. The Executor must record the rate; the Engineer sets the acceptable threshold, since it
  is a product decision, not an implementation one.
- **R-4 Prompt injection inside documents.** R6b treats document text as untrusted for R3/R4 only.
  Instructions embedded in a PDF that redirect the orchestrator are a distinct threat this task does
  not cover — out of scope here, flagged so it is not assumed covered.
- **R-5 Thread memory.** Redaction happens before `master_orchestrator` persists the turn, so PII
  never reaches the Postgres checkpointer. This is a property to assert in tests, not merely to
  claim.
- **R-6 R12 conflicts with the repo's live policy.** R12 cites `mcp/CLAUDE.md` rule 8 (mock by
  default), but `agent_core/llm.py`, `backend/CLAUDE.md` rule 6 and `docker-compose.yml`
  (`GEMMA_API_KEY:?required`) all state there is no mock fallback. Proposed reading: the
  deterministic layers are offline by construction and satisfy R12's intent for the fast path, while
  the judge follows the established always-real policy. **This is a requirement-level ambiguity —
  the Engineer confirms or corrects it at the approval gate.**

### Steps

1. Contracts and config first (R2, R10) — the verdict shape and settings surface, before any
   detector exists. Everything downstream depends on this being stable.
2. Normalization + lexicon fast path (R9, R3) — offline, deterministic, testable alone.
3. PII layer with RU recognizers and the R5 notice renderer (R4, R5, D8).
4. Judge provider behind the D3 interface, with its own timeout budget (R-1).
5. Service assembly: endpoints, decision logging without raw PII (R11), health.
6. Container + compose wiring, dependency order from both callers (A6).
7. Call site (b) — `doc_analyzer`, the narrowest and most testable of the three (D7, A3).
8. Call sites (a) and (c) — gateway, plus the contract extension outward and the fail-mode
   behaviour (D5, D6, R7, R8).
9. Fixtures and measurement: A1 corpus, A2 PII set, A5 outage path, A4 numbers recorded.

Sequencing rationale: 1-5 build a service that is complete and testable with no caller touched, so
a failure there costs nothing outside `guardrails/`. 7 precedes 8 because `doc_analyzer` exercises
the full contract (banned topics + PII + redaction + the LLM boundary) inside one process, proving
the design before the gateway's pure-proxy exception in D5 is committed to.

## v2

Patch of v1 against TASK.md Amendments v2. Decisions D1, D2, D3, D4, D7, D8 stand unchanged.

### Decisions patched

**D5 superseded — enforcement at the orchestrator entry.** Both gates move into
`master_orchestrator.services.orchestrator.Orchestrator.run`: the input gate before the
tool-calling loop is constructed, the output gate on the merged answer before it is returned.
`backend/gateway` is untouched, so `backend/CLAUDE.md` rule 2 needs no exception and the v1
approval risk disappears. The gate call belongs in `services/`, not `tools/start_job.py`
(`mcp/CLAUDE.md` rule 3) — same layering argument as D7.

**D5a (new) — ordering against thread memory.** `Orchestrator.run` both persists the turn
through the LangGraph checkpointer and runs the loop. The input gate must precede the memory
write, not merely the loop: otherwise raw PII lands in Postgres before redaction and R11/R-5
are violated in the store even though the LLM never saw it. Sequencing inside `run` is
therefore load-thread -> gate -> persist redacted -> loop, and this ordering is the thing
the R-5 test asserts.

**D6 superseded.** The single output choke point is the orchestrator's merged answer.
This is strictly narrower than v1's gateway placement: `delete_thread` and future
non-orchestrator routes are outside it, which the Engineer accepted explicitly.

**D8 extended — outward delivery.** The R5 notice and flag ride on `OrchestrationResult`,
which the gateway already forwards unchanged (`AgentData` allows extra keys). No gateway
schema change, no `_common/env` change, no contract break. The frontend reads them off the
existing response payload.

**D9 (new) — the `review` verdict (R13).** The verdict becomes three-valued:
`allowed | blocked | review`. `review` is produced only where the drug category fires and a
good-faith medical/pharmacological signal is also present; every other conflict resolves as
before. Consequences:
- The signal that distinguishes medicine from procurement is the classification problem this
  task actually has to solve. The lexicon cannot express it — a `review` verdict requires the
  judge, so this is the one path where the judge is not optional.
- `review` is terminal for the turn: the loop does not run. The turn is persisted in a held
  state so the operator's later decision has something to resolve against.
- The review record lives in the guardrails service's own store, not in the orchestrator's
  thread memory: it outlives the thread, is queried by operators rather than by `thread_id`,
  and must be subject to R11's no-raw-PII rule independently of the checkpointer.
- The service therefore gains persistence, which v1 did not have. This is the largest single
  cost of the amendment and the reason the step list below grows rather than shrinks.
- Resolution endpoint only; no moderator UI (TASK.md v2 scope line).

**R-6 closed.** R12 withdrawn — always-real is the policy; the deterministic layers remain
offline by construction, which is a property, not a requirement to satisfy.

### Impact map delta

| Area | Change vs v1 |
|---|---|
| `backend/gateway/**` | **removed from scope** — no change at all |
| `backend/_common/env` | **removed from scope** |
| `mcp/master_orchestrator/services/orchestrator.py` | both gates, ordered per D5a |
| `mcp/master_orchestrator/schemas/http.py` | `OrchestrationResult` carries R5 flag/notice + held state |
| `mcp/master_orchestrator/config.py` | guardrails endpoint, timeouts, fail-mode (R10) |
| `guardrails/` | + `review` verdict, review store, resolution endpoint (D9) |
| `frontend/` | + held/under-review state, in addition to the R5 notice |
| tests | + R13 routing, + D5a memory-ordering assertion; A5 outage re-read at the orchestrator |

### Risks patched

- **R-1, R-2, R-4 stand.** R-2 gains weight: R13 makes the judge mandatory on the medical
  path, so the segment-bounding decision now affects correctness, not just cost.
- **R-3 replaced.** No FP ceiling. The new failure mode is misrouting: a procurement request
  dressed in medical vocabulary resolving to `review` instead of `blocked`. `review` holds the
  turn rather than answering, so this degrades to latency and operator load — not to a leak.
  The inverse (a genuine medical question resolving to `blocked`) is the one A1 now forbids.
- **R-5 sharpened** into the D5a ordering assertion above.
- **R-7 (new) — held turns need an owner.** A `review` case with no operator watching is a
  request that never completes. The resolution endpoint exists in scope, but nothing in this
  task guarantees anyone is polling it. Operational ownership and any timeout-to-default
  behaviour are an Engineer decision, and the plan does not assume one.
- **R-8 (new) — the guardrails service becomes stateful.** It now needs a store, a schema and
  a migration path. Reusing the stack's existing Postgres keeps the surface small; a private
  schema keeps it from entangling with the checkpointer's tables.

### Steps patched

Steps 1-6 stand. Step 5 additionally covers the `review` verdict and its store (D9, R-8).

7. Call site R6b — `doc_analyzer` (unchanged from v1).
8. **Replaced:** orchestrator gates, ordered per D5a, plus the `OrchestrationResult` extension
   outward. Gateway work drops out entirely.
9. **Replaced:** resolution endpoint and the held-turn path end to end (D9, R-7).
10. **New:** fixtures and measurement — A1 corpus with the medical control set asserting
    `review` routing, A2 PII set, A3, A5 outage at the orchestrator, D5a memory ordering,
    A4 numbers recorded.
