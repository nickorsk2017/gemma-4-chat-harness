"""TASK A5 / R8: what the callers do when the gate itself is unreachable.

The fail policy is asymmetric on purpose, so it needs testing on both sides. These
tests point the client at a dead port rather than mocking the transport — the thing
under test is precisely what happens when the network call does not come back.
"""

from __future__ import annotations

import pytest

from agent_core import guardrails as gr

pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
def dead_gate(monkeypatch):
    """A port nothing is listening on.

    The ladder is shortened here on purpose: its *timing* is asserted in
    ``test_output_ladder_is_bounded`` with a controlled clock, and paying the real
    1 + 2 + 4 s of backoff in every outage test would buy nothing.
    """
    monkeypatch.setenv("GUARDRAILS_URL", "http://127.0.0.1:9/mcp")
    monkeypatch.setenv("GUARDRAILS_TIMEOUT_S", "1")
    monkeypatch.setenv("GUARDRAILS_RETRY_ATTEMPTS", "2")
    monkeypatch.setenv("GUARDRAILS_RETRY_BASE_S", "0.01")


async def test_input_fails_closed():
    """A prompt must not reach the model when nothing checked it."""
    with pytest.raises(gr.GuardrailsUnavailable):
        await gr.check_input("любой запрос", source="test")


async def test_output_fails_open_and_says_so():
    """The answer is released — but the verdict records why it was not checked."""
    verdict = await gr.check_output("готовый ответ", source="test")
    assert verdict.allowed
    assert verdict.text == "готовый ответ"
    assert verdict.reason and "fail-open" in verdict.reason


async def test_output_failure_is_logged_as_an_error(caplog):
    """An ungated answer is an incident, not a debug detail (TASK R8).

    The attempt count is part of the record (TASK R6): an answer released after four
    tries is a different incident from one released after none.
    """
    with caplog.at_level("ERROR", logger="agent_core.guardrails"):
        await gr.check_output("готовый ответ", source="test", thread_id="t9")
    messages = [r.getMessage() for r in caplog.records]
    assert any("ungated" in m for m in messages), "the fail-open path did not log an error"
    assert any("attempts=2" in m for m in messages), "the incident did not record attempts"


async def test_input_is_single_shot(monkeypatch):
    """TASK R6 scope: the ladder is the OUTPUT path's. A fast refusal must not become
    a slow one just because the gate is down."""
    calls = []

    async def _spy(tool, payload):
        calls.append(tool)
        return gr._Result(gr._Outcome.RETRYABLE, detail="down")

    monkeypatch.setattr(gr, "_call", _spy)
    with pytest.raises(gr.GuardrailsUnavailable):
        await gr.check_input("любой запрос", source="test")
    assert calls == ["check_input"], "the input path retried"


async def test_a_decided_verdict_is_never_retried(monkeypatch):
    """TASK R7: `blocked` decided once is decided. Retrying it would be a loophole."""
    calls = []

    async def _spy(tool, payload):
        calls.append(tool)
        return gr._Result(
            gr._Outcome.VERDICT,
            verdict=gr.Verdict(decision=gr.Decision.BLOCKED, text=""),
        )

    monkeypatch.setattr(gr, "_call", _spy)
    verdict = await gr.check_output("ответ", source="test")
    assert not verdict.allowed
    assert len(calls) == 1, "a decided verdict was retried"


async def test_a_contract_error_is_not_retried(monkeypatch):
    """TASK R7 amended (A6-1): a malformed reply is our bug; repeating it hides it."""
    calls = []

    async def _spy(tool, payload):
        calls.append(tool)
        return gr._Result(gr._Outcome.TERMINAL, detail="contract: boom")

    monkeypatch.setattr(gr, "_call", _spy)
    verdict = await gr.check_output("ответ", source="test")
    assert verdict.allowed and "fail-open" in (verdict.reason or "")
    assert len(calls) == 1, "a contract error was retried"


async def test_output_ladder_is_bounded(monkeypatch):
    """TASK R6/R8: the gaps grow by the configured factor and the phase deadline wins
    when the attempt count would have kept going."""
    monkeypatch.setenv("GUARDRAILS_RETRY_ATTEMPTS", "4")
    monkeypatch.setenv("GUARDRAILS_RETRY_BASE_S", "1")
    monkeypatch.setenv("GUARDRAILS_RETRY_FACTOR", "2")
    monkeypatch.setenv("GUARDRAILS_OUTPUT_DEADLINE_S", "60")

    slept: list[float] = []

    async def _no_sleep(seconds):
        slept.append(seconds)

    async def _down(tool, payload):
        return gr._Result(gr._Outcome.RETRYABLE, detail="down")

    monkeypatch.setattr(gr.asyncio, "sleep", _no_sleep)
    monkeypatch.setattr(gr, "_call", _down)

    result = await gr._call_with_ladder("check_output", {})
    assert result.attempts == 4, "the ladder did not use every configured attempt"
    assert slept == [1, 2, 4], f"gaps were not 1x/2x/4x: {slept}"

    # Now make the deadline, not the count, the binding constraint.
    slept.clear()
    monkeypatch.setenv("GUARDRAILS_OUTPUT_DEADLINE_S", "2")
    result = await gr._call_with_ladder("check_output", {})
    assert result.attempts < 4, "the phase deadline did not stop the ladder"
