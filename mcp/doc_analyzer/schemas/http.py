"""HTTP request / response contracts for doc_analyzer tools.

The request carries the user's ``prompt`` and the raw attached ``file`` (base64).
doc_analyzer owns the parsing: it decodes the PDF with PyPDF, then passes the
extracted text + prompt to the LLM. ``file`` is optional at the schema level so
the orchestrator's model can leave it empty (it is injected at dispatch).
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from agent_core.files import FilePayload
from agent_core.envelope import AgentResponse
from doc_analyzer.schemas.document import DocAnalysis


class AnalyzeRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Instruction about the document.")
    file: FilePayload | None = Field(
        default=None, description="The attached document (base64); injected at dispatch."
    )


AnalyzeResponse = AgentResponse[DocAnalysis]
