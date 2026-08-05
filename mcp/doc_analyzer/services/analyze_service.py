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
from agent_core.guardrails import DOCUMENT_REJECTED, check_input
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


class DocumentBlocked(ValueError):
    """The document (or the prompt about it) violates policy — no LLM call was made."""


async def analyze_document(prompt: str, file: FilePayload) -> DocAnalysis:
    """Extract the PDF's text and answer the prompt against it via gemma.

    The extracted text is untrusted input and is gated on the same terms as a user
    prompt (TASK R6b). The gate sits here, between extraction and the LLM call, and
    not in ``tools/`` — tools stay thin (mcp/CLAUDE.md rule 3) and this is the only
    layer that owns the LLM boundary.

    Only the document text is gated, not ``prompt``: the user's prompt was already
    checked at the orchestrator's input gate, and sending both concatenated forced this
    function to slice the prompt back off the redacted result — arithmetic that breaks the
    moment the gate returns the text fenced (TASK A5-1, PLAN D17).

    The verdict here is binary. A rejected document produces one fixed sentence and no
    analysis; nothing is rewritten and no cleaned document is generated.
    """
    text = _extract_pdf_text(file)

    verdict = await check_input(text, source="doc_analyzer", surface="document")
    if not verdict.allowed:
        raise DocumentBlocked(DOCUMENT_REJECTED)
    # Everything downstream uses the gate's text — the original never reaches the LLM.
    # It comes back fenced, and `system_note` is the line that says the fence is data.
    text = verdict.text
    if verdict.notice:
        text = f"{text}\n\n{verdict.notice}"

    content = ANALYZE_DOC.format(filename=file.filename, prompt=prompt, text=text)
    if verdict.system_note:
        content = f"{verdict.system_note}\n\n{content}"
    message = HumanMessage(content=content)
    reply = await get_llm().ainvoke([message])
    answer = reply.content if isinstance(reply.content, str) else str(reply.content)
    return DocAnalysis(filename=file.filename, answer=answer)
