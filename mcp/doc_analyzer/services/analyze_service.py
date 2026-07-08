"""Document analysis service.

doc_analyzer owns PDF parsing: it decodes the base64 file, extracts text with
PyPDF, then runs prompt + text through the shared gemma LLM (Novita, via
``agent_core.llm.get_llm``) using LangChain. No mocks: a missing
``GEMMA_API_KEY`` raises ``LLMConfigError`` on first LLM use.
"""

from __future__ import annotations

import io

from langchain_core.messages import HumanMessage

from agent_core.files import FilePayload
from agent_core.llm import get_llm
from doc_analyzer.prompts.analyze import ANALYZE_DOC
from doc_analyzer.schemas.document import DocAnalysis


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
    reply = await get_llm().ainvoke([message])
    answer = reply.content if isinstance(reply.content, str) else str(reply.content)
    return DocAnalysis(filename=file.filename, answer=answer)
