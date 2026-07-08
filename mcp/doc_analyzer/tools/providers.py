"""Provider behind the doc_analyzer tool.

doc_analyzer owns PDF parsing: it decodes the base64 file, extracts text with
PyPDF, then runs prompt + text through the shared gemma LLM
(``google/gemma-4-31b-it`` via Novita) using LangChain. No mocks: a missing
``GEMMA_API_KEY`` raises ``LLMConfigError`` on first LLM use.
"""

from __future__ import annotations

import io

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage

from agent_core.files import FilePayload
from agent_core.llm import build_chat_model
from doc_analyzer.config import settings
from doc_analyzer.prompts.analyze import ANALYZE_DOC
from doc_analyzer.schemas.document import DocAnalysis

_model: BaseChatModel | None = None


def _chat_model() -> BaseChatModel:
    global _model
    if _model is None:
        _model = build_chat_model(
            provider=settings.llm_provider,
            model=settings.llm_model,
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
        )
    return _model


def _extract_pdf_text(file: FilePayload) -> str:
    """Decode the base64 PDF and extract all its text with PyPDF."""
    from pypdf import PdfReader

    try:
        reader = PdfReader(io.BytesIO(file.decode_bytes()))
        chunks = [page.extract_text() or "" for page in reader.pages]
    except Exception as exc:  # noqa: BLE001 - malformed upload is a caller error
        raise ValueError(f"could not read PDF {file.filename!r}: {exc}") from exc
    text = "\n".join(c for c in chunks if c).strip()
    if not text:
        raise ValueError(
            f"{file.filename!r} contains no extractable text — if it is a scanned "
            "document, send it as an image instead"
        )
    return text


async def analyze_document(prompt: str, file: FilePayload) -> DocAnalysis:
    """Extract the PDF's text and answer the prompt against it via gemma."""
    text = _extract_pdf_text(file)
    message = HumanMessage(
        content=ANALYZE_DOC.format(filename=file.filename, prompt=prompt, text=text)
    )
    reply = await _chat_model().ainvoke([message])
    answer = reply.content if isinstance(reply.content, str) else str(reply.content)
    return DocAnalysis(filename=file.filename, answer=answer)
