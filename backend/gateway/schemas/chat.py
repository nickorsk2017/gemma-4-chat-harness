"""Chat request/response contracts.

Kept compatible with the frontend's existing shape so
``frontend/services/chatService.ts`` can adopt the real gateway without changing
its caller signature:

    request  : { "prompt": str, file?, thread_id? }   (SendMessageRequest)
    response : ApiResponse[AgentData]                  (agent result, passed through)

The gateway is a pure proxy. Attachments travel inline as base64 (``FilePayload``)
and the agent's result (``AgentData``) is forwarded unchanged. ``FilePayload``
mirrors ``agent_core.files.FilePayload`` field-for-field (the gateway may not
import ``mcp/`` packages, backend rule 7); the two are JSON-compatible across MCP.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class FilePayload(BaseModel):
    """A file carried inline as base64 (mirror of agent_core.files.FilePayload)."""

    filename: str = Field(..., description="Original file name.")
    content_type: str = Field(..., description="MIME type, e.g. 'application/pdf'.")
    content_b64: str = Field(..., description="Base64-encoded raw file bytes.")


class ChatRequest(BaseModel):
    """Payload the frontend sends when the user submits a message."""

    prompt: str = Field(..., min_length=1, description="The end-user prompt.")
    file: FilePayload | None = Field(
        default=None,
        description="Optional attachment forwarded unchanged to the orchestrator.",
    )
    thread_id: str | None = Field(
        default=None,
        description="Conversation thread key. Omit on the first message; the "
        "AGENT generates one and returns it. Send it back on follow-ups so the "
        "agent keeps history.",
    )


class AgentData(BaseModel):
    """The agent's payload, passed through the gateway unchanged.

    The gateway is a proxy: it does not compute these fields, it forwards whatever
    the agent's OrchestrationResult carried. Extra keys are allowed so the gateway
    never has to change when the agent's result grows.
    """

    model_config = {"extra": "allow"}

    answer: str = Field(default="", description="The agent's merged answer.")
    thread_id: str = Field(
        default="",
        description="Thread key the AGENT stored this turn under; clients send it "
        "with the next message to continue the conversation.",
    )


class DeleteThreadReply(BaseModel):
    """Successful payload of a thread deletion."""

    thread_id: str = Field(..., description="The thread that was deleted.")
    deleted: bool = Field(default=True, description="Always true on success.")
