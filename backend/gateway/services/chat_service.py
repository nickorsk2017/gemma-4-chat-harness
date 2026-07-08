"""Chat proxy service: bridge HTTP <-> the agent's MCP tools. No logic lives here.

The gateway is a pure proxy. This service does only transport work: turn a
multipart upload into a base64 ``FilePayload`` (the agent speaks JSON, not
multipart), forward the call to the agent, and hand the agent's outcome back to
the router. It generates no thread_id and validates no input — the agent owns
thread_id generation, prompt/file validation, routing and memory.
"""

from __future__ import annotations

import base64

from fastapi import UploadFile

from gateway.schemas.chat import FilePayload
from gateway.services.agent_client import AgentClient, AgentOutcome


class GatewayError(Exception):
    """Transport/upstream failure talking to the agent (HTTP 502)."""


class ChatService:
    """Forwards chat calls to the agent. Transport only — decides nothing."""

    def __init__(self, client: AgentClient) -> None:
        self._client = client

    async def reply(
        self, prompt: str, file: FilePayload | None = None, thread_id: str | None = None
    ) -> AgentOutcome:
        """Forward the prompt (and optional file) to the agent, unchanged."""
        return await self._client.send(prompt, file, thread_id)

    async def reply_with_files(
        self, prompt: str, files: list[UploadFile], thread_id: str | None = None
    ) -> AgentOutcome:
        """Base64-encode the (single) upload as transport, then forward.

        No validation here: empty prompt / unsupported type / oversize are the
        agent's concern. Only the multipart->base64 conversion is transport.
        """
        file = await self._encode(files)
        return await self.reply(prompt, file, thread_id)

    async def delete_thread(self, thread_id: str) -> AgentOutcome:
        """Proxy a thread deletion to the agent."""
        return await self._client.delete_thread(thread_id)

    @staticmethod
    async def _encode(files: list[UploadFile]) -> FilePayload | None:
        """Turn the first upload (if any) into a base64 FilePayload. Transport only."""
        if not files:
            return None
        file = files[0]
        data = await file.read()
        return FilePayload(
            filename=file.filename or "attachment",
            content_type=file.content_type or "application/octet-stream",
            content_b64=base64.b64encode(data).decode("ascii"),
        )
