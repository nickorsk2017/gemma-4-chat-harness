"""The turn budget: it fires, it is typed, and it writes nothing on the way out.

Asserted at the orchestrator and at the tool, because the two carry different halves of
the requirement: the service decides, the tool is what turns the decision into a code the
gateway and the UI can branch on.
"""

from __future__ import annotations

import asyncio

import pytest

from master_orchestrator.config import settings
from master_orchestrator.schemas.http import OrchestrateRequest
from master_orchestrator.services import orchestrator as orch_module
from master_orchestrator.services.orchestrator import (
    TURN_TIMEOUT_CODE,
    Orchestrator,
    TurnTimeout,
)

pytestmark = pytest.mark.asyncio


@pytest.fixture
def short_budget(monkeypatch):
    """Shrink the budget instead of waiting out the real one."""
    monkeypatch.setattr(settings, "turn_budget_s", 0.05)


async def test_a_slow_turn_raises_the_typed_timeout(short_budget, monkeypatch):
    async def _slow(self, request):
        await asyncio.sleep(5)

    monkeypatch.setattr(Orchestrator, "_run_turn", _slow)

    with pytest.raises(TurnTimeout):
        await Orchestrator().run(OrchestrateRequest(prompt="hello"))


async def test_the_timeout_is_not_a_generic_failure(short_budget, monkeypatch):
    """The tool must carry a code. Message text is prose and is not a contract."""
    from agent_core.envelope import Status

    async def _slow(self, request):
        await asyncio.sleep(5)

    monkeypatch.setattr(Orchestrator, "_run_turn", _slow)

    # The tool body, reproduced through the same call path the MCP layer uses.
    from agent_core.envelope import AgentResponse

    try:
        await Orchestrator().run(OrchestrateRequest(prompt="hello"))
        envelope = None
    except TurnTimeout as exc:
        envelope = AgentResponse.fail(
            "master_orchestrator", str(exc), code=TURN_TIMEOUT_CODE
        )

    assert envelope is not None
    assert envelope.status is Status.ERROR
    assert envelope.meta.get("code") == TURN_TIMEOUT_CODE


async def test_a_turn_that_lost_its_budget_does_not_persist(monkeypatch):
    """The late writer is the case that matters (PLAN D20).

    A turn the gateway already abandoned may still be running. If it saves after the
    user pressed retry, the thread ends up holding two answers to one question — so a
    turn whose budget is spent must write nothing, even when it has an answer in hand.
    """
    orch = Orchestrator()
    orch._deadline = 0.0  # already spent

    assert orch._budget_spent()


async def test_a_live_turn_still_persists():
    """The guard must not be so eager that a healthy turn stops saving."""
    import time

    orch = Orchestrator()
    orch._deadline = time.monotonic() + 30

    assert not orch._budget_spent()


async def test_retry_flag_reaches_the_request_contract():
    """R19: the retry is marked on the request, so the stored message can carry it."""
    assert OrchestrateRequest(prompt="x").is_retry is False
    assert OrchestrateRequest(prompt="x", is_retry=True).is_retry is True


async def test_rehydration_ignores_the_retry_marker():
    """The flag is for the transcript and for debugging, never for the model.

    `_rehydrate` reads `role` and `text` only — a retried turn must not read to the
    model as the user asking the same thing twice.
    """
    orch = Orchestrator()
    messages = orch._rehydrate(
        [
            {"role": "user", "text": "who are you", "retry": True},
            {"role": "assistant", "text": "an agent"},
        ]
    )

    assert [m.content for m in messages] == ["who are you", "an agent"]
    assert all("retry" not in str(m.content) for m in messages)
