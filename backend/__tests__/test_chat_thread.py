"""Gateway thread_id behavior: the proxy forwards it and echoes the agent's.

thread_id generation moved to the agent. The gateway forwards whatever the client
sent (including None) and returns whatever thread_id the agent reports back.
"""

from __future__ import annotations

from gateway.services.agent_client import AgentOutcome
from gateway.services.chat_service import ChatService


class FakeClient:
    """Records the thread_id forwarded; the agent supplies the returned one."""

    def __init__(self, delete_ok: bool = True) -> None:
        self.seen: list[str | None] = []
        self.deleted: list[str] = []
        self._delete_ok = delete_ok

    async def send(self, prompt, file=None, thread_id=None):
        self.seen.append(thread_id)
        # The agent generates a thread_id when none was sent and returns it.
        returned = thread_id or "agent-generated"
        return AgentOutcome(ok=True, data={"answer": "ok", "thread_id": returned})

    async def delete_thread(self, thread_id):
        self.deleted.append(thread_id)
        return AgentOutcome(ok=self._delete_ok, error=None if self._delete_ok else "boom")


async def test_missing_thread_id_forwarded_as_none_and_agent_id_returned():
    client = FakeClient()
    service = ChatService(client)
    outcome = await service.reply("hi")
    assert client.seen == [None]  # gateway does not generate one
    assert outcome.data["thread_id"] == "agent-generated"  # echoed from the agent


async def test_existing_thread_id_passes_through():
    client = FakeClient()
    service = ChatService(client)
    outcome = await service.reply("hi", None, "abc123")
    assert client.seen == ["abc123"]
    assert outcome.data["thread_id"] == "abc123"


async def test_delete_thread_is_proxied():
    client = FakeClient()
    service = ChatService(client)
    outcome = await service.delete_thread("abc123")
    assert client.deleted == ["abc123"]
    assert outcome.ok is True


async def test_delete_thread_failure_surfaces_from_agent():
    client = FakeClient(delete_ok=False)
    service = ChatService(client)
    outcome = await service.delete_thread("abc123")
    assert client.deleted == ["abc123"]
    assert outcome.ok is False and outcome.error == "boom"
