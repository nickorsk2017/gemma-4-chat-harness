"""Gateway thread_id behavior (memory plumbing): generate, forward, echo, delete."""

from __future__ import annotations

import pytest

from gateway.schemas.chat import ChatRequest
from gateway.services.chat_service import (
    ChatService,
    GatewayError,
    GatewayValidationError,
)
from gateway.services.orchestrator_client import OrchestrationOutcome


class FakeClient:
    """Records the thread_id the service forwards to the orchestrator."""

    def __init__(self, delete_ok: bool = True) -> None:
        self.seen: list[str | None] = []
        self.deleted: list[str] = []
        self._delete_ok = delete_ok

    async def orchestrate(self, prompt, context=None, thread_id=None):
        self.seen.append(thread_id)
        return OrchestrationOutcome(ok=True, answer="ok", subtasks=1)

    async def delete_thread(self, thread_id):
        self.deleted.append(thread_id)
        if self._delete_ok:
            return OrchestrationOutcome(ok=True)
        return OrchestrationOutcome(ok=False, error="boom")


async def test_thread_id_generated_forwarded_and_echoed():
    client = FakeClient()
    service = ChatService(client)
    reply = await service.reply(ChatRequest(prompt="hi"))
    assert reply.thread_id  # generated
    assert client.seen == [reply.thread_id]  # forwarded to the orchestrator


async def test_existing_thread_id_passes_through():
    client = FakeClient()
    service = ChatService(client)
    reply = await service.reply(ChatRequest(prompt="hi", thread_id="abc123"))
    assert reply.thread_id == "abc123"
    assert client.seen == ["abc123"]


async def test_delete_thread_forwards_and_acknowledges():
    client = FakeClient()
    service = ChatService(client)
    reply = await service.delete_thread("abc123")
    assert client.deleted == ["abc123"]
    assert reply.thread_id == "abc123"
    assert reply.deleted is True


async def test_delete_thread_blank_id_is_a_validation_error():
    client = FakeClient()
    service = ChatService(client)
    with pytest.raises(GatewayValidationError):
        await service.delete_thread("   ")
    assert client.deleted == []  # never reached the orchestrator


async def test_delete_thread_orchestrator_failure_maps_to_gateway_error():
    client = FakeClient(delete_ok=False)
    service = ChatService(client)
    with pytest.raises(GatewayError, match="boom"):
        await service.delete_thread("abc123")
