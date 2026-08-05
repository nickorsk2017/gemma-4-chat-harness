# TASK — 2026-08-02-guardrails-service
owner: Engineer
immutable: true

## Requirements

- R1: Introduce a standalone **guardrails service** — independently deployable, own
  distribution, own container. It is the single owner of all content-safety and
  PII policy in the system; no caller may reimplement or duplicate policy logic.
- R2: The service exposes exactly two operations, `check_input` and `check_output`,
  both taking and returning Pydantic contracts. The verdict carries: `allowed`
  (bool), `categories` (list), `score` per category, `redacted_text`, `redactions`
  (list of {type, count}), and `reason`.
- R3: **Banned topics, both directions** (input and output):
  - sexual / intimate content;
  - references to narcotics and illicit drug use.
  A verdict for a banned topic must identify the category, not merely return "blocked".
- R4: **PII detection on input.** Supported types at minimum: phone number, RU
  internal passport, SNILS, INN, email, credit card, IBAN. Detected PII is
  **redacted, not rejected** — the request proceeds with placeholders substituted.
- R5: When any PII was redacted, an **English notice** must be appended to the payload
  handed to the LLM, exactly:
  `Note: the user's personal data ({TYPES}) was not passed to the system, per policy.`
  where `{TYPES}` is the comma-separated list of detected PII types. The same fact
  must be returned to the caller as a structured flag so the frontend can surface it
  to the user.
- R6: **Three enforcement points**, all routed through the same service:
  - (a) **Gateway, pre-prompt** — the user prompt is checked *before* it reaches the
    MCP `master_orchestrator`. Nothing unchecked may enter the orchestration loop.
  - (b) **Inside the file-analysis tool** (`mcp/doc_analyzer`) — text extracted from an
    uploaded document is checked before it is passed to the LLM. Document content is
    untrusted input and is subject to the same R3/R4 policy as a user prompt.
  - (c) **Output** — the final answer is checked before it is returned to the user.
- R7: On a blocked **input**: no LLM call is made; the user receives a refusal response
  identifying that the request violates policy, without echoing the offending content.
  On a blocked **output**: the answer is replaced by a refusal response.
- R8: Failure policy is asymmetric and configurable: the **input** path is
  **fail-closed** (service unavailable or timed out => request blocked); the **output**
  path is **fail-open with a logged incident**. Timeouts are configuration, not constants.
- R9: **Russian is the primary user language** and must be supported at parity with
  English, including common evasion: transliteration, latin/cyrillic homoglyph
  substitution, and character padding.
- R10: All thresholds, category toggles, timeouts, model/provider selection and endpoints
  come from `config.py` (pydantic-settings, env-backed). No hardcoded thresholds or secrets.
- R11: Every decision is logged with category, score, latency, verdict and caller
  enforcement point. Logs must **never** contain raw detected PII — store type and
  offset only.
- R12: The service ships with a deterministic mock/offline provider so the whole system
  runs with zero external keys (`mcp/CLAUDE.md` rule 8).

## Acceptance

- A1: An adversarial corpus of >=100 cases (RU and EN, including transliteration and
  homoglyph evasion) is committed as a test fixture. Every banned-category case is
  blocked; the false-positive rate on the benign control set (medical, legal and
  pharmacological questions asked in good faith) is measured and recorded in
  VALIDATION.md.
- A2: A PII fixture covering every type in R4 is committed. Each type is redacted, the
  R5 notice string is produced verbatim with the correct `{TYPES}` list, and the
  original values appear nowhere in the payload leaving the service or in the logs.
- A3: An integration test proves enforcement point (b): a document containing banned
  content and PII, submitted through the file-analysis tool, is redacted/blocked before
  the LLM call — asserted at the LLM boundary, not merely at the tool's return value.
- A4: Latency budget is stated in PLAN.md and met under test: the fast path (no LLM
  judge invoked) is measured, and the p95 of the full input check is recorded.
- A5: With the guardrails service stopped, input requests are refused with a clear error
  and the output path degrades per R8 — both covered by tests.
- A6: `ruff` clean, unit + integration tests pass, `docker compose up` brings the new
  service up and the existing services still start and pass their checks.

## Constraints

- **No user data may leave the perimeter.** Third-party moderation SaaS (Bedrock
  Guardrails, Azure Content Safety, OpenAI moderation, Lakera) is out of scope for the
  default configuration. If the Planner wants to allow one as an optional provider, it
  must be off by default and must sit *after* PII redaction, never before.
- The repo targets Python >= 3.14, but ML/NLP wheels for 3.14 lag. The guardrails service
  may pin a different interpreter version inside its own container; it must not force a
  version change on any existing service.
- If placed under `mcp/`, the service must follow `mcp/CLAUDE.md` — folder structure,
  contracts-first, thin tools, prompts as data, config not constants, fail soft.
- All frameworks pinned to latest stable versions (root `CLAUDE.md`).
- The frontend must surface the R5 redaction notice to the user; the API contract from
  the gateway must carry it.
- Existing gateway and doc_analyzer contracts may be extended but not broken.

## Amendments — v2 (Engineer, at the HIGH approval gate)

These supersede the clauses they name. Originals above are kept for audit; where they
conflict, this section wins.

- **R6a / R6c superseded — enforcement moves out of the gateway.** Both the input gate and
  the output gate live at the `master_orchestrator` entry: input is checked before the
  tool-calling loop starts, output before the merged answer is returned. `backend/gateway`
  is not modified and keeps its pure-proxy property (`backend/CLAUDE.md` rule 2) intact.
  R6b (`doc_analyzer`) is unchanged.
  Accepted consequence: the REST surface is not guarded independently of the orchestrator —
  a caller reaching `/api/chat` still passes through the gate, but any future non-orchestrator
  route would not. Revisit if such a route is ever added.
- **R5 delivery path amended.** The redaction notice and flag travel outward inside the
  orchestrator's result, which the gateway forwards unchanged (`AgentData` already allows
  extra keys). No gateway contract change is required; the frontend constraint stands.
- **R12 withdrawn.** The repository's live policy is always-real (`agent_core/llm.py`,
  `backend/CLAUDE.md` rule 6, `docker-compose.yml` requiring `GEMMA_API_KEY`), and
  `mcp/CLAUDE.md` rule 8 is stale. No mock provider is required. Bringing `mcp/CLAUDE.md`
  into line with actual policy is a separate task, not this one.
- **R13 (new) — human in the loop for medical and pharmacological content.** The drug
  category may not auto-block when the content also carries a good-faith medical or
  pharmacological signal. Such a case resolves to a third verdict state, `review`, which
  neither blocks nor silently passes:
  - the turn is held and the user is told the request is under review;
  - the case is persisted with its categories, scores and the signal that triggered review —
    subject to R11 (no raw PII in the record);
  - a human decision (allow / block) resolves the case, and the resolution is recorded so it
    can be folded back into the A1 corpus.
  In scope here: the `review` verdict state, its persistence, an operator resolution
  endpoint, and the user-visible held state. **Out of scope: a moderator UI.**
- **A1 amended.** No false-positive ceiling is set. Instead: benign medical and
  pharmacological cases in the control set must resolve to `review` under R13, not to
  `blocked`. The measured rate is still recorded in VALIDATION.md, now as an observation
  rather than a gate.
- **A2, A3, A4, A5, A6 stand**, with A3's and A5's enforcement points re-read per the R6a/R6c
  amendment above.

## Amendments — v3 (Engineer, on VALIDATION v1 FAIL)

Resolves open issues V-1 and V-2. Both are environment limits, not defects: neither the
judge's live latency nor an image build can be exercised where the work was done, and
neither blocks the gate from being correct.

- **A4 narrowed.** Acceptance now covers the deterministic path only — the part the
  gate's own latency budget governs. Measured and recorded in VALIDATION v1: 6 ms p95 for
  a prompt, 1.1 s p95 for a 24k-character document, 5.7 s one-off warmup at startup. The
  judge-path p95 moves to `TODO.md` to be measured against live traffic; the 8 s judge
  timeout stands as a stated assumption until then.
- **A6 narrowed.** Acceptance covers tests, ruff and the compose file resolving. The
  image build — including the spaCy model downloads — moves to `TODO.md`.
- **`TODO.md` (repo root) is now the register** for everything this task deliberately
  left undone: the two above plus the document-scan cost, the hand-maintained lexicon,
  the unattended review queue, document-embedded prompt injection, the untested frontend,
  and the missing migration tooling. Written in plain language on purpose — the point is
  that it stays readable to whoever picks it up cold.
