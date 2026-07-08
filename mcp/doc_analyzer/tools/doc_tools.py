"""MCP tools for doc_analyzer. Thin: validate -> provider -> envelope."""

from __future__ import annotations

from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from agent_core.envelope import AgentResponse
from agent_core.files import FilePayload
from doc_analyzer.schemas.document import DocAnalysis
from doc_analyzer.tools import providers

AGENT = "doc_analyzer"


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def analyze_document(
        prompt: Annotated[
            str, Field(min_length=1, description="Instruction about the document.")
        ],
        file: FilePayload | None = None,
    ) -> AgentResponse[DocAnalysis]:
        """Answer a prompt about the attached PDF (extracted with PyPDF, then LLM)."""
        try:
            if file is None:
                return AgentResponse.fail(AGENT, "no document file was provided")
            result = await providers.analyze_document(prompt, file)
            return AgentResponse.ok(AGENT, result)
        except Exception as exc:  # noqa: BLE001
            return AgentResponse.fail(AGENT, str(exc))
