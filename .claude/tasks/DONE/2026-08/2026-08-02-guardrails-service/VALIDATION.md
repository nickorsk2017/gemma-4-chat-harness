# VALIDATION — 2026-08-02-guardrails-service

## v1
validation_version: 1
result: FAIL

### Acceptance

| # | Verdict | Evidence |
|---|---|---|
| A1 | PASS | 39 banned cases (RU/EN, translit, homoglyph, padding) all blocked; 16 medical cases all resolve to `review`, none to `blocked`; 12 benign pass untouched. Amended A1 asks for review-routing, not an FP ceiling — met. |
| A2 | PASS | All 7 required PII types redacted; the R5 string is asserted verbatim; the original value is asserted absent from both the outgoing text and the structured report. SNILS/INN checksums independently tested against valid and invalid inputs. |
| A3 | PASS | `mcp/tests/test_doc_analyzer_gate.py` asserts at the LLM boundary: the model stub records zero calls for a blocked document, and receives `<PHONE_NUMBER>` rather than the number for a redacted one. |
| A4 | **FAIL** | Fast path measured (below). The p95 of the *full* input check — the judge path — is not measured. See issue V-1. |
| A5 | PASS | `mcp/tests/test_gate_outage.py` drives the client at a dead port: input raises, output releases the answer, carries `fail-open` in its reason and logs at ERROR. |
| A6 | **FAIL** | Tests and ruff clean. `docker compose up` not executed. See issue V-2. |

### Measured (A4, partial)

Deterministic path, judge disabled, Presidio pattern-only, 1340 samples:

| Input | p50 | p95 | max |
|---|---|---|---|
| prompt-sized | 4.6 ms | 6.1 ms | 54.9 ms |
| document, ~24k chars | 797 ms | 1107 ms | 1107 ms |
| analyzer warmup (startup, once) | — | — | 5.7 s |

Two observations the numbers make, neither of which is visible from the code:

- **The document path is three orders of magnitude slower than the prompt path** and runs
  on every attachment. It is within the 10 s client budget with room, but it is the
  component that will move first as documents grow. PLAN R-2's cap bounds what the *judge*
  sees; it does not bound the deterministic scan, which reads the whole text.
- **Lazy analyzer construction was a live defect, found by measuring rather than by
  reading.** The first request paid the full build — tens of seconds, far past the
  callers' timeout — so the first request after every deploy would have hit the
  fail-closed path and been refused. Fixed during validation: the build now runs in the
  lifespan startup, before the service reports healthy. Re-measured above.

### Requirements

R1-R11, R13 met. R12 withdrawn by the v2 amendment. R6a/R6c verified at the amended
location (orchestrator, not gateway); `backend/gateway` is confirmed unmodified.

PLAN D5a — the ordering property — is asserted directly:
`test_redaction_happens_before_the_prompt_is_persisted` checks the recorded checkpointer
writes, not only the model call. That is the assertion that could actually fail on a
plausible wrong implementation.

### Suites

| Suite | Result |
|---|---|
| `guardrails/tests` | 182 passed |
| `mcp/tests` | 9 passed |
| `ruff` (all new/changed) | clean |

Both run in a Linux container: `mcp/.venv` points at a macOS interpreter and cannot
execute under the mounted workspace. This is why V-1 and V-2 cannot be closed here.

### Open issues

- **V-1** (`requirement`, medium) — A4's judge-path p95 is unmeasured. Closing it needs a
  live `GEMMA_API_KEY` against the real provider, which this environment does not have.
  The Engineer either runs the measurement locally or relaxes A4 to the deterministic
  path, which is the part the gate's own latency budget actually governs.
- **V-2** (`requirement`, medium) — A6's `docker compose up` half is unverified: no docker
  daemon here. The compose file parses and the service graph resolves, but the image build
  (including the two spaCy model downloads in the Dockerfile) has not been exercised.

Both are environment limitations rather than defects in the work; neither is resolvable by
the Planner or the Executor, which is why they route to the Engineer.

### Not covered, stated so it is not assumed

- Prompt injection embedded in documents (PLAN R-4) — explicitly out of scope.
- Frontend jest suite not run; the React changes are typed but unexercised.
- `review_timeout_s` auto-resolution path has no test — it is disabled by default and the
  behaviour it would trigger is still an open policy question (PLAN R-7).

## v2
validation_version: 2
result: PASS

Re-validated against TASK.md v3. Only A4 and A6 changed; v1's evidence for A1, A2, A3,
A5 and R1-R13 stands unaltered and is not restated.

| # | Verdict | Evidence |
|---|---|---|
| A4 | PASS | Narrowed to the deterministic path, which is measured and recorded in v1: 6.1 ms p95 prompt, 1107 ms p95 for a 24k-char document, 5.7 s startup warmup. |
| A6 | PASS | 182 + 9 tests pass, ruff clean, compose file parses and the service graph resolves with `mcp` gated on the gate's health. |

Confirmed on re-check: `TODO.md` exists at the repo root and carries all seven deferred
items, including the two former blockers. The amendment moved them into a register rather
than deleting them, so nothing was closed by being forgotten.

One thing worth stating plainly rather than burying: this PASS certifies that the gate
behaves correctly and that the deferred work is written down — not that the stack has
been run end to end. The first live run should watch the judge's latency and the first
request after boot, which is where the cold-start defect would have surfaced in
production had measurement not caught it here.
