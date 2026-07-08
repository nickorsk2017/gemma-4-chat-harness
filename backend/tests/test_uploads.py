"""Upload handling: the gateway proxy only base64-encodes; it never validates.

Validation (type/size/empty prompt) now lives in the agent. The gateway's sole
job for an attachment is the multipart -> base64 transport conversion.
"""

from __future__ import annotations

import base64
import io

from fastapi import UploadFile
from starlette.datastructures import Headers

from gateway.schemas.chat import FilePayload
from gateway.services.agent_client import AgentOutcome
from gateway.services.chat_service import ChatService


def _upload(name: str, content_type: str, data: bytes) -> UploadFile:
    return UploadFile(
        file=io.BytesIO(data),
        filename=name,
        headers=Headers({"content-type": content_type}),
    )


class _CaptureClient:
    """Records the file the service forwards to the agent."""

    def __init__(self) -> None:
        self.sent: list[FilePayload | None] = []

    async def send(self, prompt, file=None, thread_id=None):
        self.sent.append(file)
        return AgentOutcome(ok=True, data={"answer": "ok", "thread_id": "t"})

    async def delete_thread(self, thread_id):
        return AgentOutcome(ok=True)


async def test_pdf_is_forwarded_as_base64_not_parsed():
    client = _CaptureClient()
    service = ChatService(client)
    await service.reply_with_files("summarize", [_upload("cv.pdf", "application/pdf", b"%PDF-fake")])
    (file,) = client.sent
    assert isinstance(file, FilePayload)
    assert file.filename == "cv.pdf" and file.content_type == "application/pdf"
    assert base64.b64decode(file.content_b64) == b"%PDF-fake"


async def test_unsupported_type_is_forwarded_not_rejected():
    """The gateway does NOT validate type — it forwards; the agent decides."""
    client = _CaptureClient()
    service = ChatService(client)
    outcome = await service.reply_with_files("x", [_upload("x.txt", "text/plain", b"hi")])
    (file,) = client.sent
    assert file.content_type == "text/plain"  # forwarded as-is, no rejection
    assert outcome.ok


async def test_no_files_forwards_none():
    client = _CaptureClient()
    service = ChatService(client)
    await service.reply_with_files("hi", [])
    assert client.sent == [None]
