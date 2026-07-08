from __future__ import annotations

import base64
from enum import Enum

from pydantic import BaseModel, Field


class FileKind(str, Enum):
    """Which specialist a file is routed to."""

    DOCUMENT = "document"
    IMAGE = "image"


# content_type -> kind. The gateway validates against these before forwarding.
DOCUMENT_TYPES: dict[str, str] = {
    "application/pdf": ".pdf",
}
IMAGE_TYPES: dict[str, str] = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


def classify(content_type: str | None) -> FileKind | None:
    """Map a MIME type to the sub-agent kind, or ``None`` if unsupported."""
    if not content_type:
        return None
    if content_type in DOCUMENT_TYPES:
        return FileKind.DOCUMENT
    if content_type in IMAGE_TYPES:
        return FileKind.IMAGE
    return None


class FilePayload(BaseModel):
    """A file carried inline as base64. The single cross-boundary file contract."""

    filename: str = Field(..., description="Original file name (for display/logging).")
    content_type: str = Field(..., description="MIME type, e.g. 'application/pdf'.")
    content_b64: str = Field(..., description="Base64-encoded raw file bytes.")

    @property
    def kind(self) -> FileKind | None:
        return classify(self.content_type)

    def decode_bytes(self) -> bytes:
        """Return the raw file bytes (base64-decoded)."""
        return base64.b64decode(self.content_b64)

    def data_url(self) -> str:
        """Return a ``data:<mime>;base64,<...>`` URL (for multimodal LLM parts)."""
        return f"data:{self.content_type};base64,{self.content_b64}"
