"""Orchestrator-side rate limiting (TASK 2026-08-05-rate-limit-gateway-orchestrator,
A3): defence in depth via the `limits` package, independent of the gateway's own
`slowapi` gate (R2).

Styled on `test_turn_timeout.py`: `_run_turn` is monkeypatched to a stub so an
over-limit turn's rejection can be asserted to happen *before* it — i.e. before any
LLM call, guardrails call, or store read/write (R3).
"""

from __future__ import annotations

import uuid

import pytest

from master_orchestrator.config import settings
from master_orchestrator.schemas.http import OrchestrateRequest, OrchestrationResult
from master_orchestrator.services.orchestrator import (
    RATE_LIMITED_CODE,
    Orchestrator,
)
from agent_core.ratelimit import RateLimited

pytestmark = pytest.mark.asyncio


@pytest.fixture
def no_run_turn(monkeypatch):
    """`_run_turn` must never be reached by a rejected turn: fail the test if it is."""
    calls: list[OrchestrateRequest] = []

    async def _stub(self, request):
        calls.append(request)
        return OrchestrationResult(
            prompt=request.prompt, answer="ok", thread_id=request.thread_id or "t",
        )

    monkeypatch.setattr(Orchestrator, "_run_turn", _stub)
    return calls


async def test_an_over_limit_thread_bucket_raises_rate_limited_before_run_turn(
    no_run_turn, monkeypatch
):
    monkeypatch.setattr(settings, "rate_limit_thread_rpm", 1)
    monkeypatch.setattr(settings, "rate_limit_global_rpm", 1000)
    thread_id = uuid.uuid4().hex

    # First turn on this thread is admitted; `_run_turn` runs exactly once.
    await Orchestrator().run(OrchestrateRequest(prompt="hello", thread_id=thread_id))
    assert len(no_run_turn) == 1

    # The second turn on the SAME thread, within the same window, is rejected — and
    # never reaches `_run_turn` (no LLM call, no guardrails call, no store write).
    with pytest.raises(RateLimited):
        await Orchestrator().run(OrchestrateRequest(prompt="again", thread_id=thread_id))
    assert len(no_run_turn) == 1


async def test_an_over_limit_global_bucket_raises_rate_limited_before_run_turn(
    no_run_turn, monkeypatch
):
    monkeypatch.setattr(settings, "rate_limit_thread_rpm", 1000)
    monkeypatch.setattr(settings, "rate_limit_global_rpm", 1)

    # First turn (any thread) is admitted by the global bucket.
    await Orchestrator().run(
        OrchestrateRequest(prompt="hello", thread_id=uuid.uuid4().hex)
    )
    assert len(no_run_turn) == 1

    # A second turn on a DIFFERENT thread still hits the shared global bucket.
    with pytest.raises(RateLimited):
        await Orchestrator().run(
            OrchestrateRequest(prompt="again", thread_id=uuid.uuid4().hex)
        )
    assert len(no_run_turn) == 1


async def test_missing_thread_id_shares_one_anonymous_bucket(no_run_turn, monkeypatch):
    monkeypatch.setattr(settings, "rate_limit_thread_rpm", 1)
    monkeypatch.setattr(settings, "rate_limit_global_rpm", 1000)

    await Orchestrator().run(OrchestrateRequest(prompt="hello"))
    assert len(no_run_turn) == 1

    with pytest.raises(RateLimited):
        await Orchestrator().run(OrchestrateRequest(prompt="again"))
    assert len(no_run_turn) == 1


async def test_rate_limited_carries_a_positive_retry_after(no_run_turn, monkeypatch):
    monkeypatch.setattr(settings, "rate_limit_thread_rpm", 1)
    monkeypatch.setattr(settings, "rate_limit_global_rpm", 1000)
    thread_id = uuid.uuid4().hex

    await Orchestrator().run(OrchestrateRequest(prompt="hello", thread_id=thread_id))

    with pytest.raises(RateLimited) as excinfo:
        await Orchestrator().run(OrchestrateRequest(prompt="again", thread_id=thread_id))
    assert excinfo.value.retry_after_s > 0


async def test_disabled_buckets_never_reject(no_run_turn, monkeypatch):
    """`<=0` disables a bucket at the call site (RK6): it must never reject."""
    monkeypatch.setattr(settings, "rate_limit_thread_rpm", 0)
    monkeypatch.setattr(settings, "rate_limit_global_rpm", 0)
    thread_id = uuid.uuid4().hex

    for _ in range(5):
        await Orchestrator().run(OrchestrateRequest(prompt="hi", thread_id=thread_id))
    assert len(no_run_turn) == 5


async def test_the_rejection_maps_to_the_expected_gateway_code():
    """The tool body reproduced through the same call path start_job.py uses."""
    from agent_core.envelope import AgentResponse, Status

    exc = RateLimited(retry_after_s=7.5)
    envelope = AgentResponse.fail(
        "master_orchestrator", str(exc), code=RATE_LIMITED_CODE, retry_after_s=exc.retry_after_s
    )

    assert envelope.status is Status.ERROR
    assert envelope.meta.get("code") == RATE_LIMITED_CODE
    assert envelope.meta.get("retry_after_s") == 7.5
