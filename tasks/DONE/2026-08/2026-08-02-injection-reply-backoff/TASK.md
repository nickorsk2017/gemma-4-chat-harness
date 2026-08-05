# TASK — 2026-08-02-injection-reply-backoff
owner: Engineer
immutable: true

Follows `2026-08-02-guardrails-service`. That task built the gate and deliberately left
two holes, both named in `TODO.md`: instructions hidden inside a document are not caught,
and the output path degrades to fail-open the moment the gate does not answer. This task
closes both.

## Requirements

- R1: **Prompt injection becomes a first-class category** of the guardrails service, on the
  same footing as `sexual` and `drugs`. It is owned by the service; no caller reimplements
  it. The verdict shape does not change — a new `Category` value and a score under the same
  contract.
- R2: **Three untrusted surfaces are covered**, not one:
  - (a) the user prompt, at the existing `master_orchestrator` input gate;
  - (b) text extracted from an uploaded document, at the existing `doc_analyzer` gate —
    this is the case `TODO.md` calls out explicitly ("забудь предыдущие указания" inside a
    PDF);
  - (c) text fetched from the network by a sub-agent (web read) before it re-enters the
    orchestrator's context.
  (c) is new ground: today nothing gates a tool result on its way back in.
- R3: **Detection follows the existing cascade discipline** — deterministic layers first,
  the judge only for what they cannot settle. The clean path must not gain a new
  unbounded-latency layer. Cost per layer rises; the cheap layers must settle the common
  case alone.
- R4: **Detection is not the only defence.** Untrusted text handed to a model must be
  structurally separated from instructions: a fenced untrusted-content block plus a standing
  system rule that content inside it is data and never an instruction. The fence must not be
  closable from inside the untrusted text.
- R5: **Injection is blocked, not redacted, and the input path stays fail-closed.** The user
  gets a refusal that does not echo the payload. When the injection is document-borne, the
  refusal must say which document was rejected — a user who uploaded a poisoned file needs
  to know which one.
- R6: **Reply guardrails — the output gate is retried on exponential backoff before it is
  allowed to fail open.** Today a single unreachable call releases the answer ungated. The
  gate call is retried with a backoff that grows by a fixed factor (base × 2 × 4 × 8, factor
  and attempt count from config). The R8 fail-open policy of the previous task applies only
  after the last attempt is exhausted, and the logged incident records how many attempts
  were made.
- R7: **Only transport failures are retried.** A verdict is a verdict: `blocked` on the
  first answer is blocked. Retrying a decided verdict would be a policy loophole, not a
  robustness feature.
- R8: **The retry has a total deadline, not just an attempt count.** Exponential backoff on
  a dead gate must not add its whole ladder to every answer. A single configured ceiling
  bounds the entire output-gate phase — attempts stop when either the count or the deadline
  is reached, whichever comes first — and that ceiling must sit below the gateway's own
  request timeout.
- R9: The retry policy lives in `mcp/agent_core/guardrails.py`, next to the existing
  asymmetric fail policy. It is a property of the call, not of the caller, and not of the
  service.
- R10: All new thresholds, factors, attempt counts, deadlines and category toggles are
  env-backed configuration (`GUARDRAILS_*`), consistent with R10 of the previous task. No
  constants in code.
- R11: Injection decisions are logged with category, score, surface (prompt | document |
  tool result), attempt count and latency. The **payload is never logged** — the same rule
  that keeps raw PII out of the log applies to an injection string.

## Acceptance

- A1: An adversarial injection corpus of >=100 cases (RU and EN) is committed as a fixture
  and every case is caught. It must include, at minimum: direct override ("ignore previous
  instructions"), role reassignment, system-prompt exfiltration, delimiter/fence escape,
  homoglyph and transliteration evasion, and instructions split across lines or encodings.
- A2: A benign control set is committed and is **not** blocked — in particular, text that
  *discusses* prompt injection (documentation, a security question, this very TASK.md)
  must pass. The measured false-positive rate is recorded in VALIDATION.md.
- A3: An integration test proves R2b at the LLM boundary, not at the tool's return value: a
  document carrying embedded instructions never reaches the model.
- A4: A test proves R2c: a poisoned web result is gated before it re-enters the
  orchestrator's context.
- A5: A test proves the fence of R4 cannot be closed from inside the untrusted text.
- A6: A test with a controlled clock proves the backoff ladder: N failures produce exactly
  the configured attempts at the configured intervals, the total stays within the R8
  deadline, fail-open happens only after exhaustion, and the incident log carries the
  attempt count.
- A7: A test proves R7 — a `blocked` output verdict triggers exactly one gate call.
- A8: The clean-path latency measured in the previous task (6 ms prompt / 1.1 s for a 24k
  document) does not regress beyond noise; the new figure is recorded in VALIDATION.md.
- A9: `ruff` clean, unit + integration tests pass, existing guardrails and MCP tests still
  pass.

## Constraints

- No user data leaves the perimeter; no third-party moderation SaaS. Same as the previous
  task, and it applies to any injection classifier considered.
- `guardrails` keeps its own interpreter pin and its own distribution. Agents mirror the
  contract, never import it — the `agent_core.guardrails` mirror must stay JSON-compatible
  after the `Category` extension.
- Adding a `Category` value must not break a caller that does not know it. Old callers see
  an unknown category string, not an error.
- The injection check must be independently toggleable, and it must be possible to run it
  without the judge at all.
- Retry must not multiply cost on the input path: the input gate is already fail-closed,
  and adding a ladder there trades a fast refusal for a slow one. If the Planner wants
  backoff on input too, it is a separate decision with its own default.
- The frontend must be able to distinguish "answer withheld" from "gate unavailable, answer
  released ungated" — R6 changes how often the second happens, and it is currently invisible
  to the user.

## Open question for the Planner

R6 says the *gate call* is retried. There is a second, different reading of "reply
guardrails by exponent": that a **blocked answer is regenerated** and re-checked, up to 3
attempts, before the refusal is shown. That is a product decision, not an implementation
detail — it costs one LLM generation per attempt and it can look like the model negotiating
with its own filter. It is **out of scope here** unless the Engineer says otherwise; R7
above assumes it is out.

## Amendments — v2 (Engineer, before the Planner is dispatched)

These supersede the clauses they name. The originals above are kept for audit; where they
conflict, this section wins. No plan exists yet (`plan_version: 0`), so nothing downstream
is invalidated.

- **R8 superseded — the ceiling moves, the ladder does not.** The backoff ladder is not to be
  trimmed to fit the current gateway budget; the budget is raised to fit the ladder. The
  Planner must:
  - state the worst-case wall clock of the output-gate phase explicitly (per-attempt
    `GUARDRAILS_TIMEOUT_S` = 10 s today, plus the backoff sleeps, times the attempt count);
  - raise `GATEWAY_ORCHESTRATOR_TIMEOUT_S` (180 s today) so that the orchestrator's own
    worst case — the tool-calling loop plus the new output-gate phase — still fits inside
    it with margin, and state the new value and the arithmetic behind it;
  - check every other timeout on the path for the same clearance and name any that also
    have to move: `ORCHESTRATOR_SUBAGENT_TIMEOUT_S` (200 s), any reverse-proxy or ingress
    read timeout, and the frontend's own request abort if it has one.
  A total deadline on the output-gate phase is still required — it is what makes the worst
  case a number rather than a hope — but it is now sized from the ladder, not the reverse.
  Accepted consequence: a fully dead gate makes the slowest answers noticeably slower. That
  is the trade being bought, and it is the right one: an ungated answer is worse than a slow
  one.

- **R7 amended — retry on transport failure *or* HTTP 5xx.** A 5xx is the gate saying it
  broke, which is the same class of event as it not answering at all, and it must not
  short-circuit to fail-open. Therefore:
  - **retry**: connection error, read timeout, and any `5xx` response;
  - **do not retry**: any `2xx` carrying a verdict — `blocked` decided once is decided —
    and any `4xx`. A 4xx means the caller sent something the gate rejected as malformed;
    repeating it repeats the same error and hides a contract bug behind a delay. It is
    logged as a caller defect and falls through to the fail policy immediately.
  This requires `agent_core.guardrails._post` to stop collapsing every exception into
  `None`: the retry decision needs the status code, so the transport layer must
  distinguish these three outcomes rather than reporting one.
  A9/A7 extend accordingly: the tests must cover 500 (retried), 400 (not retried, exactly
  one call), and a decided `blocked` (not retried, exactly one call).

## Amendments — v3 (Engineer, at the HIGH approval gate)

The plan is **not approved**. Six directives change the architecture, not the wording; they
supersede what they name and route back to the Planner (`plan_version` bump). Originals kept
for audit.

- **A3-1 — `guardrails/` moves to `mcp/guardrails/`. It is an AI agent, not a neutral service.**
  This reverses D1 of `2026-08-02-guardrails-service`, which placed it outside `mcp/` for two
  named reasons. Both come back and the Planner must resolve each explicitly, not in passing:
  - *Star topology.* `mcp/CLAUDE.md` reaches sub-agents only through `master_orchestrator`, and
    `doc_analyzer` has to reach the gate directly. As an agent under `mcp/`, that is a peer call.
    Either `mcp/CLAUDE.md` gains a stated exemption for a cross-cutting gate, or the gate is
    reached some way that is not a peer call. Silently breaking the rule is not an option.
  - *Interpreter pin.* Every `mcp/` distribution requires Python >= 3.14; `guardrails` pins
    `>=3.12,<3.14` **because presidio/spaCy publish no 3.14 wheels**, and `agent_core` — which an
    `mcp/` agent is expected to share — is itself >= 3.14. A single directory move does not make
    those two numbers compatible. The Planner states which of these gives: `agent_core`'s pin, the
    PII library, or `guardrails` not sharing `agent_core`.

- **A3-2 — prompt injection is decided by the LLM, not by a dictionary.** D1/D2 of PLAN v1 are
  withdrawn: no injection phrase list, no injection automata, no `injection_block_hits`. The
  consequence is that nothing deterministic can short-circuit the injection check, so **the model
  runs on every checked text** — every prompt, every document, and every tool result. The Planner
  must state the resulting latency and cost budget as a number, per surface, including the case
  where several tool results are checked concurrently in one loop iteration. That budget is now the
  central design constraint of this task, replacing D3's surface asymmetry.

- **A3-3 — dictionaries and libraries are for masking, never for judging.** Personal data
  (passport, phone, and the rest of the R4 list) is found and replaced with a hidden placeholder by
  a library — deterministic, offline, no model involved. Keyword lists stay only as the cheap
  pre-filter of A3-4. Neither is allowed to produce a security verdict.

- **A3-4 — the agent's flow is fixed:** PII masking library -> keyword pre-filter -> LLM. The LLM
  is the only layer that decides prompt injection, performs the remaining policy checks, and
  **returns cleaned text**. The gate's output is therefore sanitised content, not merely a verdict —
  `Verdict.text` becomes the model's cleaned text where it acted, and the callers keep forwarding
  it unchanged. Masking runs first for the reason it always did: the model must never see raw
  personal data.

- **A3-5 — R13 is superseded: no held turns for medical content.** The human in the loop is the
  **doctor reading the answer**, not a moderator clearing a queue. Medical and pharmacological
  document analysis is answered normally, with a text disclaimer appended stating the data may be
  inaccurate. Consequences the Planner must carry: the `review` decision state loses its only
  producer, and with it the review store, the resolution endpoint, the held-turn copy and the
  frontend's held state. This also closes the `TODO.md` item about the unattended review queue —
  by removing the queue. **The Planner proposes whether the `review` machinery is deleted or left
  dormant; the Engineer decides that at the next gate.**

- **A3-6 — all policy lives in `guardrails`.** No caller computes, transforms or sanitises anything;
  callers pass text in and forward what comes back. This supersedes R9 and D6: the fencing and
  neutralisation of untrusted content are performed by the gate and returned in its output, not
  applied by the orchestrator's or the document analyser's prompts. The one thing that stays on the
  caller side is the retry ladder of R6 — a callee cannot retry itself — and it stays mechanical:
  transport and status codes only, no policy.

## Amendments — v4 (Engineer, resolving A3-1 and confirming A3-2)

- **A4-1 — one interpreter for the whole repository: `>=3.12,<3.14`.** The pin moves down to the
  range the masking library can actually run on, rather than the library moving up to a version it
  has no wheels for. In scope: `backend/pyproject.toml`, `mcp/agent_core`, every `mcp/*` agent, and
  `guardrails` (which already sits there and does not change). The `Python >= 3.14` line in
  `mcp/CLAUDE.md`'s stack conventions and the equivalent statement in the root `CLAUDE.md` are
  rewritten to match — a rule that contradicts the shipped pins is worse than no rule. Container
  base images follow: `guardrails/Dockerfile` is already `python:3.12-slim`, the others must be
  brought to the same base rather than left implicit.
  This closes the A3-1 pin question. Consequence accepted: nothing in the repo may use a 3.13 or
  3.14 language feature, and the upgrade is deferred until presidio/spaCy publish 3.14 wheels. The
  Planner records that as a `TODO.md` entry rather than a silent assumption.
  **A3-1's star-topology question is NOT closed by this** and still needs the Planner's answer.

- **A4-2 — A3-2 is confirmed, not to be re-litigated.** The model on every checked text is the
  accepted design. The Planner still states the latency and cost numbers per surface (they drive
  the timeout arithmetic and the R6 ladder), but it does not propose a cheaper alternative and does
  not reintroduce a deterministic injection short-circuit.

## Amendments — v5 (Engineer, resolving D13)

- **A5-1 — the document surface is gated on input only, and the verdict there is binary.** No
  cleaning, no rewriting, no span editing on document text. `mcp/doc_analyzer` passes the extracted
  text through the gate once, before the analysis; if the gate finds banned content or an injection,
  the agent returns a single fixed sentence naming what was found — *"the document contains sexual /
  narcotic content"* — and performs no analysis. Otherwise the analysis runs and its result is
  returned normally.
  This settles what A3-4's "returns cleaned text" means where it was most expensive: it does not
  apply to documents. Span-level cleaning stays on the prompt and the outbound answer, where the text
  has to survive the check and its length is bounded.
  The canned sentence names the category deliberately — a user who uploaded the file needs to know
  why it was refused — and still echoes none of the content, which is what R7 of the previous task
  actually forbids.
  **Open at this gate:** whether the tool-result gate still applies to `doc_analyzer`'s return now
  that the document is checked on the way in. The Planner recommends no.

## Amendments — v6 (Engineer, approving PLAN v2)

PLAN v2 is **approved**. The four questions it left open are settled here, each taking the Planner's
recommendation.

- **A6-1 — R7 is restated in envelope terms (D10).** Retry on transport failure, timeout, or a
  response envelope whose `status` is an internal error. Do not retry an envelope carrying a verdict,
  nor one reporting a validation or contract error. The HTTP wording of Amendments v2 is superseded;
  the intent — transient failures retry, decided verdicts and caller bugs do not — is unchanged.

- **A6-2 — the tool-result gate does not apply to `doc_analyzer`'s return.** The document is checked
  on the way in and its return is our own model's answer about already-checked input; a second model
  call there buys nothing. The gate stays on `web_agent` results, which carry third-party content.
  `image_analyzer` remains ungated and this is recorded in `TODO.md` as an open hole, not treated as
  covered — nothing in the system reads image content for policy, and no requirement here changes
  that.

- **A6-3 — the `review` machinery is deleted, not left dormant.** The store, the resolution endpoint,
  the held-turn copy and the frontend held state go. The `TODO.md` entry about the unattended queue is
  removed along with them, since the queue no longer exists.

- **A6-4 — A8 is replaced.** No regression gate against the old 6 ms / 1.1 s figures: they measured a
  fast path this task removes deliberately. Instead the Executor measures the new floor per surface —
  prompt, document, tool result, and the outbound answer — and records it in VALIDATION.md as a fresh
  baseline. The number that must be *verified* rather than merely recorded is R-7's: whether
  concurrent tool-result checks are actually served in parallel, since D15's 95 s worst case rests on
  it.

## Amendments — v7 (Engineer)

- **A7-1 — every string the user reads is English.** The two refusals, the medical
  disclaimer and the document-rejection sentence are written in English, not Russian.
  This does **not** touch R9 of the previous task: R9 requires the gate to *detect*
  Russian at parity with English, including transliteration and homoglyph evasion, and
  that requirement is unchanged — it governs what the gate understands, not what language
  it answers in. The R5 notice was already required to be English verbatim, so the effect
  of this amendment is that the user-facing surface stops being half one language and half
  the other.

## Amendments — v8 (Engineer, reverting A4-1)

- **A8-1 — A4-1 is withdrawn. The repository is back on `>=3.14`.** The premise it rested
  on was stale: `presidio-analyzer` 2.2.364 declares Python 3.14 support and excludes
  spacy 3.8.14, the single release that dropped its cp314 wheels. spacy 3.8.13 and
  thinc 8.3.12/8.3.13 all ship cp314, so the chain resolves without a repo-wide downgrade.
  Reverted: eight `requires-python` pins, three image bases, the `Makefile` guard and its
  operator messages, and the language lines in `mcp/CLAUDE.md` and `backend/CLAUDE.md`.
  **The constraint does not disappear, it moves**: `presidio-analyzer>=2.2.364` /
  `presidio-anonymizer>=2.2.364` is now a load-bearing floor, not a version bump. On an
  older presidio a 3.14 resolve picks spacy 3.8.14 and fails to build. The comment beside
  the pin says so, because the next person to relax it will not otherwise know.
  The spaCy NLP engine itself stays optional and off in tests (`GUARDRAILS_PII_USE_NLP`) —
  every R4 type is a pattern plus a checksum and needs no NER. Removing it outright was
  offered and not taken.

## Amendments — v9 (Engineer)

- **A9-1 — spaCy is removed, and presidio goes with it.** Not by preference:
  `presidio-analyzer` depends on spaCy unconditionally, with no extra to opt out of, so the
  two were never separable. The argument for removing spaCy is the one that decided it —
  spaCy's NER is a statistical model, the same class of guarantee as an LLM, weaker on
  Russian, and carrying thinc, blis, numpy and two model downloads behind it. It was never
  on the deterministic side of the line it was being kept for.
  The split is now **structured vs unstructured**, not library vs model:
  - **structured** (phone, RU passport, SNILS, INN, email, card, IBAN) — regex plus
    checksum, in `detectors/pii.py`, masked *before* any model call. SNILS, INN and
    passport validators were already ours; Luhn, IBAN mod-97 and the email pattern replace
    what presidio's built-ins supplied. Presidio's overlap resolution and replacement were
    never used — this file always had its own.
  - **unstructured** (names, addresses) — the gate's own model, returned as `pii` spans
    alongside its verdict and masked by the gate.
  **Two caveats, recorded rather than buried:**
  1. The model *sees* a name in order to find it. Structured types never reach a model at
     all; names now reach exactly one — the gate's. What this buys is that nothing
     downstream (the answering model, the checkpointer, the traces) sees them. **This is
     only within the perimeter if the gate's model is in it.** `judge_base_url` today is
     `https://api.novita.ai/openai`, which is not — so until it points at a local model,
     names leave the perimeter and the previous task's constraint is not met for them.
  2. R5's notice is required verbatim and says the data "was not passed to the system".
     That stays true for the structured types and is not literally true for names. The
     wording is not changed here because R5 fixes it; flagged for a decision.
