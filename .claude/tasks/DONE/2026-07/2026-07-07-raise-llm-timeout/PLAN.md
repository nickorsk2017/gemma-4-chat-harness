# PLAN — 2026-07-07-raise-llm-timeout

## v1

### Cause
doc_analyzer sends the whole extracted PDF text in one prompt to gemma; the LLM
call `build_chat_model(timeout=LLM_REQUEST_TIMEOUT_S)` uses 45s (compose/.env),
max_retries=1. Large context -> >45s -> "Request timed out". User chose option B:
raise the timeout.

### Effective knob
`ORCHESTRATOR_SUBAGENT_TIMEOUT_S` is referenced only in .env/compose, never in
*.py (grep-confirmed) — it is documentation, not an enforced budget. The only
real timeout is `LLM_REQUEST_TIMEOUT_S` (agent_core.llm._request_timeout ->
ChatOpenAI timeout). So the fix is to raise that value where it takes effect.

### Precedence (why root .env matters)
compose sets `LLM_REQUEST_TIMEOUT_S: "${LLM_REQUEST_TIMEOUT_S:-45}"`. The user's
root `.env` sets `LLM_REQUEST_TIMEOUT_S=45`, which WINS over the compose default.
So we must change the root .env value, not just the default.

### Change set (config only)
1. root `.env`: `LLM_REQUEST_TIMEOUT_S=45` -> `=90` (sed on that exact line only;
   no other line / secret touched). Subagent var is absent there -> inherits the
   new compose default (200), no edit needed.
2. docker-compose.yml: defaults `:-45` -> `:-90` (LLM), `:-120` -> `:-200`
   (subagent).
3. mcp/.env.example: `LLM_REQUEST_TIMEOUT_S=45` -> `90`;
   `ORCHESTRATOR_SUBAGENT_TIMEOUT_S=120` -> `200`; keep the 2x comment (still true:
   180 < 200).

### Value choice
90 = agent_core.llm.DEFAULT_REQUEST_TIMEOUT_S (aligns runtime with the code's own
default). 2x90=180 < 200 keeps the documented invariant. Trade-off: a hung
endpoint now fails after up to 2x90s; acceptable for document analysis.

### Note / follow-up
Raising the timeout mitigates but does not bound latency for very large PDFs;
if 90s still times out, options A (truncate PDF text) or C (map-reduce) remain.
Out of scope here.

### Validation
grep all three files for the new values; assert 2x90<200 arithmetically; confirm
root .env has no other diff (only line 22 changed) and secrets intact.
