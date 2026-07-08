"""PromptGenerator — builds the turn's system prompts from the payload.

The agent inserts the incoming payload (``OrchestrateRequest``) into this class,
which decides the system prompt(s) deterministically:
- a file present -> classify it (PDF or Image) and add the matching processing
  directive so the model routes to analyze_document / analyze_image;
- no file        -> add the "get data from the internet" directive (search_web).

Prompt text lives in ``prompts/orchestrate.py`` (prompts are data, mcp/CLAUDE.md
rule 4); this class only selects and orders it.
"""

from __future__ import annotations

from agent_core.files import FileKind
from master_orchestrator.prompts.orchestrate import (
    GET_FROM_INTERNET_SYSTEM,
    ORCHESTRATOR_SYSTEM,
    PROCESS_IMAGE_SYSTEM,
    PROCESS_PDF_SYSTEM,
)
from master_orchestrator.schemas.http import OrchestrateRequest


class PromptGenerator:
    """Turns one payload into the ordered list of system prompts for the turn."""

    def __init__(self, request: OrchestrateRequest) -> None:
        self._request = request

    def system_messages(self) -> list[str]:
        """Base prompt + the payload-driven directive (file kind, or internet)."""
        return [ORCHESTRATOR_SYSTEM, self._directive()]

    def _directive(self) -> str:
        file = self._request.file
        if file is None:
            return GET_FROM_INTERNET_SYSTEM
        if file.kind is FileKind.DOCUMENT:
            return PROCESS_PDF_SYSTEM
        if file.kind is FileKind.IMAGE:
            return PROCESS_IMAGE_SYSTEM
        # Unsupported kind: never reached in the loop (validated first), but keep a
        # safe default rather than raising here.
        return GET_FROM_INTERNET_SYSTEM
