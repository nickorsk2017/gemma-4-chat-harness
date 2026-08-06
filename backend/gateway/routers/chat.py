"""Chat REST endpoints. Thin proxy: forward to the agent, wrap in the envelope.

The gateway decides nothing. Each endpoint forwards the call to the agent and
maps the agent's transport outcome to an ``ApiResponse``: success -> 200, an
agent-reported failure (including validation) -> 502. Success is 200.
"""

from __future__ import annotations

import math
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import JSONResponse

from _common.env import Settings, get_settings
from _common.schemas import ApiResponse
from gateway.schemas.chat import AgentData, ChatRequest, DeleteThreadReply
from gateway.services.agent_client import RATE_LIMITED_CODE, TURN_TIMEOUT_CODE, AgentOutcome
from gateway.services.chat_service import ChatService
from gateway.services.agent_client import build_agent_client
from gateway.services.ratelimit import default_limit_value, limiter

router = APIRouter(prefix="/api", tags=["chat"])


def get_chat_service(settings: Settings = Depends(get_settings)) -> ChatService:
    """Build a ChatService from the config-selected agent client."""
    return ChatService(build_agent_client(settings))


def _fail(
    status_code: int,
    error_text: str,
    error_code: str | None = None,
    retry_after_s: float | None = None,
) -> JSONResponse:
    """Failed envelope with an honest HTTP status code.

    ``retry_after_s``, when given, becomes a whole-second ``Retry-After`` header
    (ceiling, minimum 1) — the one place both 429 sources (the gateway's own
    slowapi rejection and the orchestrator's) compute the header (PLAN D5).
    """
    response = JSONResponse(
        status_code=status_code,
        content=ApiResponse.fail(error_text, error_code).model_dump(mode="json"),
    )
    if retry_after_s is not None:
        response.headers["Retry-After"] = str(max(1, math.ceil(retry_after_s)))
    return response


def _reply(outcome: AgentOutcome) -> JSONResponse | ApiResponse[AgentData]:
    """Map an agent outcome to the REST envelope (proxy passthrough of data)."""
    if not outcome.ok:
        # 504 for the one failure the client can act on: the turn ran out of time and
        # re-sending it is a sensible thing to offer. Everything else stays 502.
        if outcome.error_code == TURN_TIMEOUT_CODE:
            return _fail(504, outcome.error or "the turn ran out of time", TURN_TIMEOUT_CODE)
        # The orchestrator's own rate-limit rejection (R2/R3), mapped the same way the
        # gateway's own slowapi rejection is: 429 + Retry-After, same envelope + code.
        if outcome.error_code == RATE_LIMITED_CODE:
            retry_after = outcome.retry_after_s if outcome.retry_after_s is not None else 1.0
            return _fail(429, outcome.error or "rate limit exceeded", RATE_LIMITED_CODE, retry_after)
        return _fail(502, outcome.error or "agent failed", outcome.error_code)
    return ApiResponse.ok(AgentData(**outcome.data))


@router.post("/chat", response_model=ApiResponse[AgentData])
@limiter.limit(default_limit_value)
async def chat(
    request: Request,
    payload: ChatRequest,
    service: ChatService = Depends(get_chat_service),
):
    """Forward a user prompt to the agent and return its answer."""
    try:
        outcome = await service.reply(
            payload.prompt, payload.file, payload.thread_id, payload.is_retry
        )
        return _reply(outcome)
    except Exception as exc:  # noqa: BLE001 - structured, never an unhandled 500
        return _fail(500, f"unexpected error: {exc}")


@router.post("/chat/files", response_model=ApiResponse[AgentData])
@limiter.limit(default_limit_value)
async def chat_with_files(
    request: Request,
    prompt: Annotated[str, Form(description="User prompt.")],
    files: Annotated[list[UploadFile], File(description="Image/PDF attachment.")],
    thread_id: Annotated[
        str | None,
        Form(description="Conversation thread key; omit to start a new thread."),
    ] = None,
    is_retry: Annotated[
        bool, Form(description="True when re-sending a turn that ran out of time.")
    ] = False,
    service: ChatService = Depends(get_chat_service),
):
    """Forward a prompt with an image/PDF attachment to the agent."""
    try:
        outcome = await service.reply_with_files(prompt, files, thread_id, is_retry)
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
