"""Chat REST endpoints. Thin proxy: forward to the agent, wrap in the envelope.

The gateway decides nothing. Each endpoint forwards the call to the agent and
maps the agent's transport outcome to an ``ApiResponse``: success -> 200, an
agent-reported failure (including validation) -> 502. Success is 200.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import JSONResponse

from _common.env import Settings, get_settings
from _common.schemas import ApiResponse
from gateway.schemas.chat import AgentData, ChatRequest, DeleteThreadReply
from gateway.services.agent_client import AgentOutcome
from gateway.services.chat_service import ChatService
from gateway.services.agent_client import build_agent_client

router = APIRouter(prefix="/api", tags=["chat"])


def get_chat_service(settings: Settings = Depends(get_settings)) -> ChatService:
    """Build a ChatService from the config-selected agent client."""
    return ChatService(build_agent_client(settings))


def _fail(status_code: int, error_text: str) -> JSONResponse:
    """Failed envelope with an honest HTTP status code."""
    return JSONResponse(
        status_code=status_code,
        content=ApiResponse.fail(error_text).model_dump(mode="json"),
    )


def _reply(outcome: AgentOutcome) -> JSONResponse | ApiResponse[AgentData]:
    """Map an agent outcome to the REST envelope (proxy passthrough of data)."""
    if not outcome.ok:
        return _fail(502, outcome.error or "agent failed")
    return ApiResponse.ok(AgentData(**outcome.data))


@router.post("/chat", response_model=ApiResponse[AgentData])
async def chat(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service),
):
    """Forward a user prompt to the agent and return its answer."""
    try:
        outcome = await service.reply(request.prompt, request.file, request.thread_id)
        return _reply(outcome)
    except Exception as exc:  # noqa: BLE001 - structured, never an unhandled 500
        return _fail(500, f"unexpected error: {exc}")


@router.post("/chat/files", response_model=ApiResponse[AgentData])
async def chat_with_files(
    prompt: Annotated[str, Form(description="User prompt.")],
    files: Annotated[list[UploadFile], File(description="Image/PDF attachment.")],
    thread_id: Annotated[
        str | None,
        Form(description="Conversation thread key; omit to start a new thread."),
    ] = None,
    service: ChatService = Depends(get_chat_service),
):
    """Forward a prompt with an image/PDF attachment to the agent."""
    try:
        outcome = await service.reply_with_files(prompt, files, thread_id)
        return _reply(outcome)
    except Exception as exc:  # noqa: BLE001 - structured, never an unhandled 500
        return _fail(500, f"unexpected error: {exc}")


@router.delete("/chat/threads/{thread_id}", response_model=ApiResponse[DeleteThreadReply])
async def delete_chat_thread(
    thread_id: str,
    service: ChatService = Depends(get_chat_service),
):
    """Delete a conversation thread by its key (proxied to the agent)."""
    try:
        outcome = await service.delete_thread(thread_id)
        if not outcome.ok:
            return _fail(502, outcome.error or "thread deletion failed")
        return ApiResponse.ok(DeleteThreadReply(thread_id=thread_id, deleted=True))
    except Exception as exc:  # noqa: BLE001 - structured, never an unhandled 500
        return _fail(500, f"unexpected error: {exc}")


@router.get("/health", response_model=ApiResponse[dict])
async def health() -> ApiResponse[dict]:
    """Liveness probe."""
    return ApiResponse.ok({"status": "up"})
