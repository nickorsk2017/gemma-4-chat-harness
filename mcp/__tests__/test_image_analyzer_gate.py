"""The output gate inside image_analyzer (TASK A1-A4).

Asserted at the service boundary, because that is where the decision is made: the tool
is deliberately unchanged (PLAN D3), so testing through it would assert the envelope
rather than the branch.

The gate stub replaces ``check_output`` **on the service module**, which is the name the
service resolves at call time (PLAN R-4). Patching ``agent_core.guardrails.check_output``
instead would leave the service's own from-imported reference in place and every case
here would pass while enforcing nothing.
"""

from __future__ import annotations

import base64

import pytest

from agent_core.files import FilePayload
from agent_core.guardrails import IMAGE_REJECTED, Decision, Redaction, Verdict
from image_analyzer.services import analyze_service

pytestmark = pytest.mark.asyncio

ANSWER = "a red bicycle leaning on a blue fence"


def _image() -> FilePayload:
    """A one-pixel PNG. The bytes never matter — the model is stubbed."""
    png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    )
    return FilePayload(
        filename="pic.png",
        content_type="image/png",
        content_b64=base64.b64encode(png).decode("ascii"),
    )


@pytest.fixture(autouse=True)
def llm(monkeypatch):
    """Stub the vision model the way test_doc_analyzer_gate.py does."""

    class _Model:
        async def ainvoke(self, messages):
            class _R:
                content = ANSWER

            return _R()

    monkeypatch.setattr(analyze_service, "get_llm", lambda: _Model())


def _gate(monkeypatch, verdict: Verdict) -> list[dict]:
    """Replace the gate with one returning `verdict`; return the recorded calls."""
    calls: list[dict] = []

    async def _stub(text, *, source, thread_id=None, known_pii_types=None):
        calls.append(
            {
                "text": text,
                "source": source,
                "thread_id": thread_id,
                "known_pii_types": known_pii_types,
            }
        )
        return verdict

    monkeypatch.setattr(analyze_service, "check_output", _stub)
    return calls


async def test_allowed_answer_is_returned_unchanged(monkeypatch):
    """A1: with an allowing gate the agent behaves exactly as it did before the gate."""
    calls = _gate(monkeypatch, Verdict(decision=Decision.ALLOWED, text=ANSWER))

    result = await analyze_service.analyze_image("what is this?", _image())

    assert result.answer == ANSWER
    assert result.filename == "pic.png"
    # R1: the answer really went through the gate, tagged with this agent.
    assert calls and calls[0]["text"] == ANSWER
    assert calls[0]["source"] == "image_analyzer"


async def test_blocked_answer_becomes_the_refusal_and_echoes_nothing(monkeypatch):
    """A2: the fixed sentence, and no fragment of what the model said."""
    _gate(
        monkeypatch,
        Verdict(decision=Decision.BLOCKED, categories=["sexual"], text="redacted"),
    )

    result = await analyze_service.analyze_image("describe it", _image())

    assert result.answer == IMAGE_REJECTED
    for word in ("bicycle", "fence", "red"):
        assert word not in result.answer.lower(), "the refusal echoed the blocked answer"


async def test_blocked_answer_is_not_an_agent_failure(monkeypatch):
    """A2 (envelope half): a verdict is not an error — PLAN D3, against doc_analyzer.

    The tool must not have grown an exception path: a blocked answer arrives as a normal
    ``ImageAnalysis``, so ``AgentResponse.ok`` carries it.
    """
    from agent_core.envelope import Status
    from image_analyzer.schemas.image import ImageAnalysis

    _gate(monkeypatch, Verdict(decision=Decision.BLOCKED))

    result = await analyze_service.analyze_image("describe it", _image())

    assert isinstance(result, ImageAnalysis)
    # The tool wraps whatever the service returns; nothing raised means status stays ok.
    from agent_core.envelope import AgentResponse

    assert AgentResponse.ok("image_analyzer", result).status is Status.OK


async def test_allowed_verdict_never_rewrites_the_answer(monkeypatch):
    """A3: redactions and rewritten text are ignored on the allowed branch (R4)."""
    _gate(
        monkeypatch,
        Verdict(
            decision=Decision.ALLOWED,
            text="a red bicycle leaning on a <REDACTED> fence",
            redactions=[Redaction(type="location", count=1)],
            notice="one item was redacted",
        ),
    )

    result = await analyze_service.analyze_image("what is this?", _image())

    assert result.answer == ANSWER, "the gate's redacted text replaced the answer"
    assert "REDACTED" not in result.answer
    assert "redacted" not in result.answer


async def test_unreachable_gate_releases_the_answer_and_logs_the_incident(
    monkeypatch, caplog
):
    """A4: the real client's fail-open, not a stub of it.

    Stubbing a fail-open verdict here would test the stub. The ladder is clamped so the
    test pays no backoff — its timing is asserted in test_gate_outage.py.
    """
    monkeypatch.setenv("GUARDRAILS_URL", "http://127.0.0.1:9/mcp")
    monkeypatch.setenv("GUARDRAILS_TIMEOUT_S", "1")
    monkeypatch.setenv("GUARDRAILS_RETRY_ATTEMPTS", "1")
    monkeypatch.setenv("GUARDRAILS_RETRY_BASE_S", "0.01")

    with caplog.at_level("ERROR", logger="agent_core.guardrails"):
        result = await analyze_service.analyze_image("what is this?", _image())

    assert result.answer == ANSWER, "an unreachable gate must not block the answer (R6)"
    messages = [r.getMessage() for r in caplog.records]
    assert any("ungated" in m for m in messages), "the ungated release was not recorded"
    assert any("source=image_analyzer" in m for m in messages), "the incident lost the agent"
