# VALIDATION — 2026-08-02-injection-reply-backoff

## v1 — Static pass. **Verdict withheld**, not given.

`status` stays `PENDING` and `stage` stays `EXECUTED` on purpose. A `PASS` here would be a
lie — A1, A2, A8 and A9 all name things that must be *run*, and nothing has been. A `FAIL`
would be a different lie: it would report a defect where there is an environment limit,
burn an iteration against `max_iterations`, and re-route work that is not wrong. The
honest state is validation in progress, and this file records the half that could be done
without a running stack.

### Requirement coverage — what is implemented

| Req | Where | Note |
|---|---|---|
| R1 injection is a first-class category | `schemas/verdict.py`, `prompts.py` | decided by the model per A3-2 |
| R2a prompt gate | `Orchestrator.run` | pre-existing, now passes `surface` |
| R2b document gate | `doc_analyzer.analyze_service` | input-only and binary per A5-1 |
| R2c tool-result gate | `Orchestrator._gate_result` | `web_agent` only, per A6-2 |
| R3 cascade discipline | — | **superseded by A3-2**: no deterministic short-circuit remains |
| R4 fencing | `services/fence.py` | applied by the gate per A3-6 |
| R5 document rejection names the file's fault | `DOCUMENT_REJECTED` | names the category, echoes nothing |
| R6 output ladder | `agent_core.guardrails._call_with_ladder` | 4 attempts, 1/2/4 s |
| R7 retry only transient | `_call` → `_Outcome` | envelope-based per A6-1 |
| R8 total deadline | `_phase_deadline` | count and deadline, whichever binds first |
| R9 policy in the gate | — | **amended by A3-6**: only the ladder stayed caller-side |
| R10 env-backed config | `config.py`, `agent_core.guardrails` | no policy constant in code |
| R11 logging without payload | `pipeline._log` | surface added; no text, ever |

Nothing in TASK.md is unimplemented. Three requirements were superseded by later
amendments rather than met as originally written, and each is marked above.

### Defects found by reading, and fixed

- **`_gate_result` named the wrong cause.** A dropped tool result was labelled "violates
  policy", but the gate also returns `blocked` when its *own* model is unavailable
  (fail-closed). The marker went into the model's context and would have gone into an
  operator's eyes, and it names a false positive where there was an outage. Now: "did not
  pass the safety gate", which is true of both.
- **A stale stub signature.** `stub_gate._check_input` in `test_guardrail_gates.py` had no
  `surface` parameter. It passes today only because the input gate does not pass one
  positionally — the next test that exercises `_gate_result` through `run()` would have
  failed on an unexpected keyword, and the failure would have read as a product bug.
- **The input gate now passes `surface="prompt"` explicitly.** It was relying on the
  default. The value is logged and branched on; a default is the wrong way to carry it.

### What cannot be validated here, and what each would catch

- `make dev-install` — the repo-wide 3.12 pin against real wheels. Green per the Engineer
  for step 0, but `agent_core` gained `fastmcp` and `guardrails` lost `fastapi`/`sqlalchemy`
  since.
- `pytest mcp/guardrails`, `pytest mcp` — the cascade, the fence, the ladder, the gates.
- `GEMMA_API_KEY=... pytest tests/test_injection_corpus.py -q -s` — **A1 and A2**. Numbers
  go here, in this file, when they exist.
- `docker compose build && up` — the relocated image, the `./mcp` build context, and the
  TCP healthcheck that replaced `/v1/health`.
- **R-7's concurrency assumption.** D15's 95 s worst case holds only if concurrent
  tool-result checks are served in parallel by a single-instance gate whose upstream has
  its own rate limit. This is the one number that is load-bearing and unmeasured, and it
  should be the first thing exercised, not the last.

### Two predictions

Recorded before the fact so they can be scored rather than rationalised afterwards:

1. `CallToolResult.structured_content` for `AgentResponse[Verdict]` may not be the flat
   model dump the client assumes. If it is wrapped, every gate call classifies as
   `TERMINAL` (a contract error) — which fails *closed* on input and *open* on output, so
   the symptom would be refused prompts and ungated answers at the same time.
2. The Host shims in `agent_core.http_server` were tuned against `mcp:8100`. `guardrails:8200`
   is admitted through `http_allowed_hosts`, but that path has never been exercised for a
   second service.

### Weakened, deliberately, and recorded so it is not discovered later

The guardrails healthcheck no longer proves the gate answers — only that something holds
the port. `/v1/health` was a GET; the MCP endpoint is a session protocol. A compose-level
check that opens an MCP session would be better and is not in this task.

### First real datum: the guard fired, and the pin is justified — but not the way A4-1 assumed

`make dev-install` refused a 3.14.3 interpreter. That is `PY_RANGE_CHECK` working: the
upper bound is new, and refusing loudly is what it is for.

Checked against PyPI rather than assumed (this is the claim A4-1 rested on, and it was
worth verifying rather than inheriting):

| package | latest | wheels at latest | has cp314 at |
|---|---|---|---|
| `spacy` | 3.8.14 | cp310–cp313 | 3.8.13, 3.8.11 |
| `thinc` | 9.1.1 | cp310–cp312 | 8.3.9, 8.3.12, 8.3.13 |
| `cymem`, `preshed`, `murmurhash`, `srsly`, `blis` | latest | incl. cp314 | latest |
| `presidio-analyzer` / `-anonymizer` | 2.2.364 | pure python, `<3.15` | n/a |

So the blocker is narrower than "presidio/spaCy have no 3.14 wheels". Everything under
spaCy already ships cp314; **`thinc` and `spacy` themselves regressed** — their *latest*
releases dropped the tag their own earlier releases had.

That reframes A4-1 without overturning it. A 3.14 stack is reachable, but only by pinning
`spacy==3.8.13` and `thinc` back to 8.3.x — deliberately not-latest, which contradicts the
root `CLAUDE.md` rule that frameworks track latest stable. Trading a version-pin rule for
an interpreter-pin rule is an Engineer decision, not a Validator one. Recorded here so the
choice is made on the table rather than discovered in a build log.

Unblocking is unaffected either way: the images are already `python:3.12-slim`, so only the
native path needs `PYTHON=python3.12`.

### First test runs: no product defect, two real ones found beside them

Both runs failed for one cause and it is not the code. `pytest` ran under the active
`.venv-gemma` (Python 3.14), where nothing is installed — `make dev-install` had refused
that interpreter minutes earlier, so `presidio_analyzer` and `langchain_core` were never
there. 106 failures, one traceback repeated; the 83 that passed are the layers that touch
neither (`normalize`, `lexicon`).

Two defects surfaced while reading why, and both are mine:

- **V-1 — `dev-install-mcp` never installed the gate.** Its agent list is hardcoded and
  did not gain `./mcp/guardrails` when step 1 moved it there. Fixed, with a note that the
  spaCy *models* are deliberately not downloaded by the target: the suite runs pattern-only
  and the images fetch them at build time.
- **V-2 — the docker-free stack has never had a gate at all.** `make dev` starts mcp,
  backend and frontend; `GUARDRAILS_URL` was never set, so it kept the compose default
  `http://guardrails:8200/mcp`, which does not resolve on a host. The input path is
  fail-closed, so **every prompt on `make dev` was refused**. This predates the task —
  the gate only ever ran in Docker — but it becomes worse here, because the tool-result
  gate would drop every web result too. Fixed: `guardrails` is a fourth dev process,
  started before the orchestrator and waited on, and the orchestrator is told where it is.

Neither was caught by `py_compile`, by the suites, or by a compose build. Both live in the
one place nothing exercises: the path a developer takes on their own machine.

### R-7 — attested by the Engineer, number pending

The Engineer reports the concurrency assumption checked and holding: concurrent
tool-result checks are served in parallel, so D15's per-iteration term is one budget
rather than one per tool, and the 95 s worst case stands as calculated.

Recorded as an **attestation, not a measurement** — no figure was supplied, and the
distinction matters for the one number the timeout arithmetic rests on. When the observed
value exists (concurrent checks in one iteration, and the wall clock they took), it
replaces this paragraph. Until then D15's 95 s is arithmetic confirmed by inspection, not
by a stopwatch.

### V-3 — A4-1 rests on a stale premise. The downgrade was avoidable.

Asked what spaCy is for, and the answer turns out to undermine the interpreter decision.

**What it does here: nothing that R4 needs.** spaCy is presidio's NLP engine — NER for
PERSON / LOCATION / ORG / DATE and context words that raise a match's confidence. Every
type R4 actually lists (phone, RU passport, SNILS, INN, email, credit card, IBAN) is a
regex plus a checksum. The repo already knew this: `pii_use_nlp` exists, and the suite has
always run with `GUARDRAILS_PII_USE_NLP=false`.

**And the 3.14 wall is upstream's, already fixed.** `presidio-analyzer` 2.2.364 declares:

    spacy!=3.7.0,!=3.8.14,<4.0.0,>=3.4.4; python_version >= "3.14"
    spacy!=3.7.0,<4.0.0,>=3.4.4;          python_version <  "3.14"

It excludes exactly the spaCy release that dropped cp314 wheels. The chain resolves:
spacy 3.8.13 ships cp314 and wants `thinc>=8.3.12,<8.4.0`; thinc 8.3.12 and 8.3.13 both
ship cp314. The repo's own constraint is `presidio-analyzer>=2.2.355`, so it would have
picked this up on its own.

I checked wheel tags and did not check dependency metadata. That is the error: "latest
spaCy has no cp314 wheels" is true and was the wrong question. A4-1 downgraded seven
distributions and two images for a constraint the ecosystem had already routed around, and
the cost landed on the Engineer as a toolchain that stopped working.

Three ways out, and the choice is the Engineer's:

1. **Revert A4-1.** Back to `>=3.14` everywhere, `python:3.14-slim` images. Everything else
   in the tree has cp314: `pyahocorasick`, and fastmcp/langchain are pure python.
2. **Drop the NLP engine as well as the pin.** Pattern-only presidio, permanently: no
   spaCy, no thinc, no two model downloads in the image. Loses PERSON-name detection,
   which R4 never asked for. This is the smallest system and the fastest image.
3. **Leave it.** 3.12 works and is the least motion, at the price of a repo pinned below
   its own toolchain for a reason that is no longer true.

### V-4 — the presidio-free layer shipped with two regressions. Caught before delivery.

The rewrite was checked by running the new `pii.py` standalone against the committed
`PII_CASES`, with `settings` and `Redaction` stubbed. Two of the seven types came back
undetected, and neither would have been visible by reading:

- **SNILS and INN stopped being detected entirely.** The port kept presidio's base scores
  (0.4 and 0.3) and applied the 0.5 threshold to them — but presidio promotes a span whose
  `validate_result` passes to full confidence, which is why those numbers worked there.
  Fixed by making the promotion explicit: a passing checksum sets the score to 1.0.
- **The card and IBAN placeholders ate the following space.** `(?:\d[ \-]?){13,19}` ends on
  an optional separator, so `<CREDIT_CARD>срок` came out glued. Both patterns now end on a
  digit.

Re-run after the fix: seven of seven detected and removed, four negative controls (16
digits failing Luhn, a one-digit-off card, nine digits, a one-digit-off IBAN) correctly
ignored, spacing intact, notice and leak detection unchanged.

The first is the instructive one: the numbers were copied faithfully and the rule that gave
them meaning was left behind. No compile step can see that. Only the old fixture run
against the new code does.

Tests added: five checksum negatives, a spacing assertion, and five on the model-PII path
(masked name, notices merged not replaced, hallucinated span ignored, the toggle, and a
junk entity type falling back to `PERSON` rather than interpolating into the placeholder —
which forced the entity name to become a three-value whitelist).

## v2 — Final verdict: PASS, on the Engineer's decision, and scoped

The Engineer closes the task and moves the remaining work to a new one. `PASS` is recorded
on that instruction, and it is worth being exact about what it covers, because a `PASS`
that reads as "verified" would misrepresent this.

**What PASS covers.** Every requirement in `TASK.md` as amended through v9 is implemented,
and each of the three that were superseded rather than met is marked as such in the
coverage table above. Two defects were found by reading and fixed (the tool-result marker
naming the wrong cause; a stale stub signature). Two more were found by *running* the
rewritten PII layer against the committed fixture and fixed (checksum promotion lost in the
port; patterns eating the trailing space). Two were found in the developer path and fixed
(`dev-install` never installed the gate; `make dev` never started it, so the docker-free
stack refused every prompt). The pin decision was reversed on evidence after its premise
turned out to be stale.

**What PASS does not cover, and what is now `TODO.md`'s.** No suite has been executed by
the Validator: this environment cannot install packages, build images or reach a model.
A1 and A2 — the injection corpus and its control set — have never run against a live model,
so detection recall and false-positive rate are unknown. The 95 s worst case is arithmetic.
The concurrency assumption underneath it is attested by the Engineer, not measured. The
gate's model is still outside the perimeter, so unstructured PII leaves it. There is no
degraded mode with the model down, no bound on model-dictated spans, no eval harness for a
prompt that now *is* the policy, and the healthcheck proves only that a port is held.

All of it is written into `TODO.md` in plain language, and the follow-up task is scoped.
Closing with the debt named is the point of closing this way; closing with it implied would
not have been.
