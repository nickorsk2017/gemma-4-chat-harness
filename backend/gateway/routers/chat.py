"""Chat REST endpoints. Thin: validate -> service -> envelope.

Errors keep the ``ApiResponse`` envelope body but carry honest HTTP status
codes: 400 for client/validation problems, 502 for orchestration/upstream
failures, 500 for unexpected exceptions. Success is 200.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import JSONResponse

from _common.env import Settings, get_settings
from _common.schemas import ApiResponse
from gateway.schemas.chat import ChatReply, ChatRequest, DeleteThreadReply
from gateway.services.chat_service import (
    ChatService,
    GatewayError,
    GatewayValidationError,
)
from gateway.services.orchestrator_client import build_orchestrator_client

router = APIRouter(prefix="/api", tags=["chat"])


def get_chat_service(settings: Settings = Depends(get_settings)) -> ChatService:
    """Build a ChatService from the config-selected orchestrator client."""
    return ChatService(build_orchestrator_client(settings), settings)


def _fail(status_code: int, error_text: str) -> JSONResponse:
    """Failed envelope with an honest HTTP status code."""
    return JSONResponse(
        status_code=status_code,
        content=ApiResponse.fail(error_text).model_dump(mode="json"),
    )


@router.post("/chat", response_model=ApiResponse[ChatReply])
async def chat(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service),
):
    """Send a user prompt to the orchestrator and return the merged answer."""
    try:
        reply = await service.reply(request)
        return ApiResponse.ok(reply)
    except GatewayValidationError as exc:
        return _fail(400, str(exc))
    except GatewayError as exc:
        return _fail(502, str(exc))
    except Exception as exc:  # noqa: BLE001 - structured, never an unhandled 500
        return _fail(500, f"unexpected error: {exc}")


@router.post("/chat/files", response_model=ApiResponse[ChatReply])
async def chat_with_files(
    prompt: Annotated[str, Form(description="Mandatory user prompt.")],
    files: Annotated[list[UploadFile], File(description="Image/PDF attachment.")],
    thread_id: Annotated[
        str | None,
        Form(description="Conversation thread key; omit to start a new thread."),
    ] = None,
    service: ChatService = Depends(get_chat_service),
):
    """Send a prompt with an image/PDF attachment to the orchestrator.

    The prompt is mandatory — attachments are never processed without one.
    """
    try:
        reply = await service.reply_with_files(prompt, files, thread_id)
        return ApiResponse.ok(reply)
    except GatewayValidationError as exc:
        return _fail(400, str(exc))
    except GatewayError as exc:
        return _fail(502, str(exc))
    except Exception as exc:  # noqa: BLE001 - structured, never an unhandled 500
        return _fail(500, f"unexpected error: {exc}")


@router.delete("/chat/threads/{thread_id}", response_model=ApiResponse[DeleteThreadReply])
async def delete_chat_thread(
    thread_id: str,
    service: ChatService = Depends(get_chat_service),
):
    """Delete a conversation thread (messages + stored documents) by its key."""
    try:
        reply = await service.delete_thread(thread_id)
        return ApiResponse.ok(reply)
    except GatewayValidationError as exc:
        return _fail(400, str(exc))
    except GatewayError as exc:
        return _fail(502, str(exc))
    except Exception as exc:  # noqa: BLE001 - structured, never an unhandled 500
        return _fail(500, f"unexpected error: {exc}")


@router.get("/health", response_model=ApiResponse[dict])
async def health() -> ApiResponse[dict]:
    """Liveness probe."""
    return ApiResponse.ok({"status": "up"})
