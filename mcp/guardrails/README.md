# guardrails

The single owner of content-safety and PII policy for agent-chat. Callers forward its
verdict; none of them re-implement the rules.

## Why it is an agent, and why it is exempt from the star

It is an MCP agent under `mcp/`, like the others — but not a *domain* agent. `mcp/` is a
star topology, and the rule that keeps sub-agents from calling each other exists to keep
the call graph acyclic. `doc_analyzer` has to reach the gate directly, which is a peer
edge; it is safe because the gate calls nobody, so an edge into it closes no cycle. That
is the single cross-cutting exemption stated in `mcp/CLAUDE.md`, and it is the only one.

It keeps its own image rather than joining `agent-chat/mcp`, and is reached over
streamable-HTTP on 8200 rather than spawned over stdio, because `doc_analyzer` — itself a
subprocess — cannot spawn it. The image carries no ML stack: since TASK A9-1 structured PII
is regex plus checksum and unstructured PII is the model's job, so presidio, spaCy and the
two language-model downloads are gone.

## Enforcement points

| Where | What is checked |
|---|---|
| `master_orchestrator.Orchestrator.run`, before the tool-calling loop | the user prompt |
| `doc_analyzer.analyze_service`, between extraction and the LLM call | the document text |
| `master_orchestrator.Orchestrator._dispatch`, on a tool's return | third-party text re-entering the context |
| `master_orchestrator.Orchestrator.run`, on the merged answer | the answer |

The input gate runs before the turn is persisted, not merely before the model call —
otherwise raw PII reaches the Postgres checkpointer even though the model never sees it.
`mcp/tests/test_guardrail_gates.py` asserts that ordering.

## The cascade

    normalize -> PII redact -> lexicon -> judge

Each layer is more expensive than the last, and the judge — the only unbounded-latency
layer — runs only on what the deterministic layers cannot settle. PII runs before the
lexicon and the judge so that no layer, including a third-party model call, ever sees a
phone number.

## Two verdicts, and a disclaimer

`allowed | blocked`. There is no third state and no moderator queue: the human in the
loop on the medical path is the **doctor reading the answer**. Where the drug category
fires *and* the content reads as a good-faith clinical question, the turn is answered and
the reply carries a disclaimer saying the information may be inaccurate. A clinical
question naming no controlled substance trips nothing and is simply allowed.

The disclaimer is rendered here, in `schemas/verdict.py`, and travels in the verdict's
`notice` — the same field and the same single-owner rule as the PII notice. When both
apply, both are shown: a redaction that happened does not stop being true because the
topic is clinical.

## Failure policy

Asymmetric, and it lives in `agent_core.guardrails` because it is a property of the call
rather than of the caller: input is fail-closed, output is fail-open with a logged
incident. One exception, and it is deliberate — a clinical question when the judge is
unavailable is answered with the disclaimer, not blocked.

## Retry, and where it lives

The output gate is retried on an exponential backoff before it is allowed to fail open —
a single unreachable call releasing an answer ungated was the defect. Only transient
failures retry: transport, timeout, or an envelope reporting an internal error. A verdict
is never retried, and neither is a contract error. The ladder is bounded twice, by attempt
count and by a phase deadline, and it lives in `agent_core.guardrails` because a callee
cannot retry itself.

## Running

    pip install ../agent_core && pip install .[dev]
    python -m pytest tests -q
    python -m guardrails.main

Configuration is entirely env-backed; see `.env.example`.
