"""HTTP request / response contracts for image_analyzer tools.

The request carries the user's ``prompt`` and the raw attached ``file`` (base64).
image_analyzer sends the image + prompt to the multimodal LLM. ``file`` is
optional at the schema level so the orchestrator's model can leave it empty (it
is injected at dispatch).
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from agent_core.files import FilePayload
from agent_core.envelope import AgentResponse
from image_analyzer.schemas.image import ImageAnalysis


class AnalyzeImageRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Instruction about the image.")
    file: FilePayload | None = Field(
        default=None, description="The attached image (base64); injected at dispatch."
    )


AnalyzeImageResponse = AgentResponse[ImageAnalysis]
