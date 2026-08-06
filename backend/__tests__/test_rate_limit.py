"""Gateway rate limiting (TASK 2026-08-05-rate-limit-gateway-orchestrator, A1/A2).

Drives real HTTP requests through the FastAPI app (slowapi's middleware + the
per-route decorator only fire on a real `Request`), with the agent client swapped
for a fake via dependency override so the assertion that the agent was never
called is meaningful.
"""

from __future__ import annotations

from starlette.testclient import TestClient

from _common.env import get_settings
from gateway.main import create_app
from gateway.routers.chat import get_chat_service
from gateway.services.agent_client import AgentOutcome
from gateway.services.chat_service import ChatService


class _CountingClient:
    """Records every call; the test asserts on how many actually reached it."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    async def send(self, prompt, file=None, thread_id=None, is_retry=False):
        self.calls.append(prompt)
        return AgentOutcome(ok=True, data={"answer": "ok", "thread_id": "t"})

    async def delete_thread(self, thread_id):
        return AgentOutcome(ok=True)


def _client_for(remote_addr: str, fake_client: _CountingClient) -> TestClient:
    """One TestClient bound to a fixed fake remote address (slowapi's default key)."""
    app = create_app()
    app.dependency_overrides[get_chat_service] = lambda: ChatService(fake_client)
    return TestClient(app, client=(remote_addr, 12345))


def test_over_limit_client_gets_429_and_never_reaches_the_agent(monkeypatch):
    monkeypatch.setattr(get_settings(), "rate_limit_default", "2/minute")
    fake = _CountingClient()
    client = _client_for("1.2.3.4", fake)

    ok1 = client.post("/api/chat", json={"prompt": "hello"})
    ok2 = client.post("/api/chat", json={"prompt": "hello again"})
    blocked = client.post("/api/chat", json={"prompt": "one too many"})

    assert ok1.status_code == 200
    assert ok2.status_code == 200
    assert blocked.status_code == 429
    body = blocked.json()
    assert body["status"] == "Failed"
    assert body["error_code"] == "rate_limited"
    retry_after = int(blocked.headers["Retry-After"])
    assert retry_after > 0
    # Only the two admitted calls ever reached the agent.
    assert fake.calls == ["hello", "hello again"]


def test_a_second_client_is_unaffected_by_the_first(monkeypatch):
    monkeypatch.setattr(get_settings(), "rate_limit_default", "1/minute")
    fake_a = _CountingClient()
    fake_b = _CountingClient()
    client_a = _client_for("10.0.0.1", fake_a)
    client_b = _client_for("10.0.0.2", fake_b)

    ok_a = client_a.post("/api/chat", json={"prompt": "hi from a"})
    blocked_a = client_a.post("/api/chat", json={"prompt": "again from a"})
    ok_b = client_b.post("/api/chat", json={"prompt": "hi from b"})

    assert ok_a.status_code == 200
    assert blocked_a.status_code == 429
    assert ok_b.status_code == 200
    assert fake_a.calls == ["hi from a"]
    assert fake_b.calls == ["hi from b"]


def test_health_is_never_rate_limited(monkeypatch):
    monkeypatch.setattr(get_settings(), "rate_limit_default", "1/minute")
    fake = _CountingClient()
    client = _client_for("5.5.5.5", fake)

    # Exhaust the /api/chat bucket for this remote address, then hammer /api/health.
    client.post("/api/chat", json={"prompt": "hi"})
    for _ in range(5):
        response = client.get("/api/health")
        assert response.status_code == 200
