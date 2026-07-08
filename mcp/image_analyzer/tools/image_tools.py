"""MCP tools for image_analyzer. Thin: validate -> provider -> envelope."""

from __future__ import annotations

from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from agent_core.envelope import AgentResponse
from agent_core.files import FilePayload
from image_analyzer.schemas.image import ImageAnalysis
from image_analyzer.tools import providers

AGENT = "image_analyzer"


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def analyze_image(
        prompt: Annotated[
            str, Field(min_length=1, description="Instruction about the image.")
        ],
        file: FilePayload | None = None,
    ) -> AgentResponse[ImageAnalysis]:
        """Answer a prompt about the attached image via the multimodal LLM."""
        try:
            if file is None:
                return AgentResponse.fail(AGENT, "no image file was provided")
            result = await providers.analyze_image(prompt, file)
            return AgentResponse.ok(AGENT, result)
        except Exception as exc:  # noqa: BLE001
            return AgentResponse.fail(AGENT, str(exc))
