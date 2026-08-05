"""Client for the guardrails agent, shared by every agent that must gate text.

Contracts are MIRRORED here, not imported: ``guardrails`` is a separate distribution and
no agent may import another. This is the same mirroring precedent as ``FilePayload``
across the gateway/MCP boundary — the two sides stay JSON-compatible by contract.

Two policies live here because both are properties of the *call*, not of the caller:

* **Fail policy (TASK R8).** An unreachable gate blocks on the INPUT path (fail-closed)
  and passes with a logged incident on the OUTPUT path (fail-open).
* **Retry ladder (TASK R6).** The output path retries once before it is allowed to fail
  open, because a single unreachable call releasing an answer ungated is the defect this
  closes. The gap is flat, not exponential: with two attempts there is one gap, and it
  exists to let a restarting gate come back — growth would only add wall clock. Only
  transient failures retry — a verdict is a verdict, and a contract error repeated is
  still a contract error.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel, Field, ValidationError

from agent_core.envelope import AgentResponse, Status

log = logging.getLogger("agent_core.guardrails")


class Decision(str, Enum):
    ALLOWED = "allowed"
    BLOCKED = "blocked"


class Redaction(BaseModel):
    type: str
    count: int = 1


class Verdict(BaseModel):
    """Mirror of ``guardrails.schemas.verdict.Verdict``."""

    model_config = {"extra": "allow"}

    decision: Decision = Decision.ALLOWED
    categories: list[str] = Field(default_factory=list)
    scores: dict[str, float] = Field(default_factory=dict)
    text: str = ""
    redactions: list[Redaction] = Field(default_factory=list)
    notice: str | None = None
    reason: str | None = None
    latency_ms: int = 0

    @property
    def allowed(self) -> bool:
        return self.decision is Decision.ALLOWED

    @property
    def redacted_types(self) -> list[str]:
        return [r.type for r in self.redactions]


class GuardrailsUnavailable(RuntimeError):
    """The gate could not be reached and the call site is fail-closed."""


# --- configuration (TASK R10: no policy constant is hardcoded) ----------------------

def _base_url() -> str:
    """MCP endpoint of the guardrails agent (streamable-HTTP, path /mcp)."""
    return os.environ.get("GUARDRAILS_URL", "http://guardrails:8200/mcp").rstrip("/")


def _timeout() -> float:
    """Per-attempt budget. 15s = the gate's own 8s judge budget plus transport and
    scheduling; below that a healthy-but-thinking gate reads as an outage."""
    return float(os.environ.get("GUARDRAILS_TIMEOUT_S", "15"))


def _attempts() -> int:
    return max(1, int(os.environ.get("GUARDRAILS_RETRY_ATTEMPTS", "2")))


def _backoff_base() -> float:
    return float(os.environ.get("GUARDRAILS_RETRY_BASE_S", "1"))


def _backoff_factor() -> float:
    return float(os.environ.get("GUARDRAILS_RETRY_FACTOR", "1"))


def _phase_deadline() -> float:
    """Ceiling on the whole output-gate phase — what makes the worst case a number.

    Attempts stop when either the count or this deadline is reached, whichever comes
    first. It must stay ABOVE one complete ladder (2 x 15s + 1s gap = 31s) or it cuts the
    last attempt short, and below the turn budget that contains it.
    """
    return float(os.environ.get("GUARDRAILS_OUTPUT_DEADLINE_S", "35"))


# --- transport ----------------------------------------------------------------------

class _Outcome(Enum):
    """Three outcomes, not two — the retry decision cannot be made without them."""

    VERDICT = "verdict"
    RETRYABLE = "retryable"   # transport, timeout, or an envelope reporting an error
    TERMINAL = "terminal"     # a contract error: repeating it repeats the bug


@dataclass
class _Result:
    outcome: _Outcome
    verdict: Verdict | None = None
    detail: str = ""
    attempts: int = 0


async def _call(tool: str, payload: dict) -> _Result:
    """One attempt. Never raises; classifies instead."""
    from fastmcp import Client

    try:
        async with Client(_base_url()) as client:
            result = await client.call_tool(
                tool, {"request": payload}, timeout=_timeout(), raise_on_error=False
            )
    except Exception as exc:  # noqa: BLE001 - the classification decides, not the type
        return _Result(_Outcome.RETRYABLE, detail=f"transport: {exc}")

    if getattr(result, "is_error", False):
        return _Result(_Outcome.RETRYABLE, detail="tool call reported an error")

    raw = result.structured_content or {}
    try:
        envelope = AgentResponse[Verdict].model_validate(raw)
    except ValidationError as exc:
        # The gate answered with something that is not our contract. Retrying sends the
        # same request and hides the mismatch behind a delay.
        return _Result(_Outcome.TERMINAL, detail=f"contract: {exc}")

    if envelope.status is Status.ERROR:
        return _Result(_Outcome.RETRYABLE, detail=envelope.error or "gate internal error")
    if envelope.data is None:
        return _Result(_Outcome.TERMINAL, detail="ok envelope carried no verdict")
    return _Result(_Outcome.VERDICT, verdict=envelope.data)


async def _call_with_ladder(tool: str, payload: dict) -> _Result:
    """The R6 ladder: base, then base x factor, x factor... bounded twice over.

    Bounded by the attempt count AND by the phase deadline, because an attempt count
    alone does not bound wall clock once the per-attempt timeout is in play.
    """
    started = time.monotonic()
    deadline = started + _phase_deadline()
    delay = _backoff_base()
    attempts = _attempts()

    result = _Result(_Outcome.RETRYABLE, detail="no attempt made")
    for attempt in range(1, attempts + 1):
        result = await _call(tool, payload)
        result.attempts = attempt
        if result.outcome is not _Outcome.RETRYABLE:
            return result
        if attempt == attempts or time.monotonic() + delay >= deadline:
            break
        await asyncio.sleep(delay)
        delay *= _backoff_factor()
    return result


# --- call sites ---------------------------------------------------------------------

async def check_input(
    text: str,
    *,
    source: str,
    surface: str = "prompt",
    thread_id: str | None = None,
) -> Verdict:
    """Gate text on its way to the LLM. Raises when the gate is down (fail-closed).

    Single-shot on purpose: the input path already refuses when the gate is unreachable,
    and a ladder here would only trade a fast refusal for a slow one.
    """
    result = await _call(
        "check_input",
        {
            "text": text,
            "direction": "input",
            "source": source,
            "surface": surface,
            "thread_id": thread_id,
        },
    )
    if result.outcome is _Outcome.VERDICT and result.verdict is not None:
        return result.verdict
    log.warning("guardrails unavailable on the input path: %s", result.detail)
    raise GuardrailsUnavailable(
        "the safety gate is unavailable; the request cannot be processed"
    )


async def check_output(
    text: str,
    *,
    source: str,
    thread_id: str | None = None,
    known_pii_types: list[str] | None = None,
) -> Verdict:
    """Gate an answer on its way out.

    Fail-open applies only after the ladder is exhausted, and the incident records how
    many attempts were made — an ungated answer is an incident, and one that happened
    after four tries is a different incident from one that happened after none.
    """
    result = await _call_with_ladder(
        "check_output",
        {
            "text": text,
            "direction": "output",
            "source": source,
            "thread_id": thread_id,
            "known_pii_types": known_pii_types or [],
        },
    )
    if result.outcome is _Outcome.VERDICT and result.verdict is not None:
        return result.verdict
    log.error(
        "guardrails unavailable on the output path; answer released ungated "
        "(source=%s thread=%s attempts=%d reason=%s)",
        source,
        thread_id,
        result.attempts,
        result.detail,
    )
    return Verdict(
        decision=Decision.ALLOWED, text=text, reason="gate unavailable (fail-open)"
    )


# User-facing copy for the two non-allowed outcomes. Never echoes the offending
# content (TASK R7). English per A7-1 — R9's parity requirement is about detecting
# Russian input, not about the language the user is answered in.
REFUSAL_INPUT = (
    "This request violates the service's terms of use and was not processed."
)
REFUSAL_OUTPUT = (
    "This answer cannot be shown: it violates the service's terms of use."
)

# What `doc_analyzer` returns when the gate rejects an uploaded document (TASK A5-1).
# Names the category so the user knows why the file was refused; echoes no content.
DOCUMENT_REJECTED = (
    "The document contains sexual or narcotic content and was not analysed."
)

# What `image_analyzer` returns when the OUTPUT gate rejects the vision model's answer
# (2026-08-03-image-analyzer-output-gate R3, PLAN D1). Unlike DOCUMENT_REJECTED this
# names no category: the output verdict carries them, but echoing them back describes
# the picture the gate just refused to describe.
IMAGE_REJECTED = (
    "This image cannot be described: the description violates the service's terms of use."
)
