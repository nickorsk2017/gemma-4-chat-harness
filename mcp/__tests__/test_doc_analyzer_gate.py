"""Enforcement point (b): the gate sits between extraction and the LLM (TASK A3).

Asserted at the LLM boundary — the tool returning an error envelope would also be
true of an implementation that called the model first and discarded the answer.
"""

from __future__ import annotations

import base64
import io

import pytest

from agent_core.files import FilePayload
from agent_core.guardrails import Decision, Redaction, Verdict
from doc_analyzer.services import analyze_service

pytestmark = pytest.mark.asyncio


def _pdf(text: str) -> FilePayload:
    """A one-page PDF carrying `text`, built without a PDF writer dependency."""
    from pypdf import PdfWriter

    try:
        from reportlab.pdfgen import canvas
    except ImportError:  # pragma: no cover
        pytest.skip("reportlab not installed")

    buf = io.BytesIO()
    pdf = canvas.Canvas(buf)
    pdf.drawString(72, 720, text)
    pdf.save()

    out = io.BytesIO()
    writer = PdfWriter(clone_from=io.BytesIO(buf.getvalue()))
    writer.write(out)
    return FilePayload(
        filename="doc.pdf",
        content_type="application/pdf",
        content_b64=base64.b64encode(out.getvalue()).decode("ascii"),
    )


@pytest.fixture
def llm_spy(monkeypatch):
    calls: list = []

    class _Model:
        async def ainvoke(self, messages):
            calls.append(messages)

            class _R:
                content = "ok"

            return _R()

    monkeypatch.setattr(analyze_service, "get_llm", lambda: _Model())
    return calls


async def test_banned_document_never_reaches_the_llm(monkeypatch, llm_spy):
    async def _check_input(text, *, source, thread_id=None):
        assert source == "doc_analyzer"
        return Verdict(decision=Decision.BLOCKED, text="", reason="lexicon: drugs")

    monkeypatch.setattr(analyze_service, "check_input", _check_input)

    with pytest.raises(analyze_service.DocumentBlocked):
        await analyze_service.analyze_document("сделай выжимку", _pdf("kupit narkotiki"))

    assert llm_spy == [], "the model was called for a blocked document"


async def test_document_pii_is_redacted_before_the_llm(monkeypatch, llm_spy):
    async def _check_input(text, *, source, thread_id=None):
        assert "+7 916 123-45-67" in text, "the gate was not given the extracted text"
        return Verdict(
            decision=Decision.ALLOWED,
            text="сделай выжимку\n\nконтакт <EMAIL_ADDRESS>",
            redactions=[Redaction(type="EMAIL_ADDRESS", count=1)],
            notice="Note: the user's personal data (EMAIL_ADDRESS) was not passed "
            "to the system, per policy.",
        )

    monkeypatch.setattr(analyze_service, "check_input", _check_input)

    await analyze_service.analyze_document(
        "сделай выжимку", _pdf("kontakt +7 916 123-45-67")
    )

    sent = " ".join(str(m.content) for m in llm_spy[0])
    assert "+7 916 123-45-67" not in sent
    assert "<EMAIL_ADDRESS>" in sent
    assert "per policy." in sent
