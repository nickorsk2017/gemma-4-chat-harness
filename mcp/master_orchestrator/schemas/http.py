"""Request/response contracts for the start_job tool.

The gateway invokes ``start_job`` with ``{"request": {prompt, file?, thread_id?}}``
and reads back an ``AgentResponse[OrchestrationResult]`` (agent_core envelope).
The file (if any) is carried inline as a base64 ``FilePayload`` and forwarded to
the chosen sub-agent unchanged — the orchestrator never decodes it.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from agent_core.files import FilePayload


class OrchestrateRequest(BaseModel):
    """One orchestration turn."""

    prompt: str = Field(..., min_length=1, description="The end-user prompt.")
    file: FilePayload | None = Field(
        default=None,
        description="Optional attachment (base64), routed unchanged to a sub-agent.",
    )
    thread_id: str | None = Field(
        default=None, description="Conversation key; groups message history."
    )


class SubTaskResult(BaseModel):
    """One executed sub-agent tool call (for observability, not memory)."""

    tool: str = Field(..., description="Sub-agent tool name the model invoked.")
    ok: bool = Field(default=True, description="Whether the call succeeded.")
    output: str = Field(default="", description="Raw sub-agent envelope text.")


class OrchestrationResult(BaseModel):
    """Merged answer plus the sub-tasks the model ran to produce it."""

    prompt: str
    answer: str
    thread_id: str = Field(
        ..., description="Thread key this turn was stored under (agent-generated "
        "when the request omitted one); returned so the client can continue."
    )
    results: list[SubTaskResult] = Field(default_factory=list)
