"""Attachment service: validate the inbound file and inject it at dispatch.

Extracted from the orchestrator so the tool-calling loop carries no file logic.
The orchestrator routes on the file's kind (Document vs Image) but delegates the
two file concerns to this service: (a) validate the attachment once before the loop
(supported kind + size within cap) and (b) inject the raw payload into a
file-consuming sub-agent's args at dispatch. The bytes are never decoded to be
processed here — injection passes the payload through unchanged as a plain dict over
MCP/JSON; validation only reads the file's kind and its decoded size.
"""

from __future__ import annotations

from agent_core.files import FilePayload
from master_orchestrator.config import settings


class FileService:
    """Validates and injects the request's optional attachment (stateless)."""

    def validate(self, file: FilePayload | None) -> None:
        """Reject an unsupported or oversized attachment; no-op when absent.

        The prompt is already enforced non-empty by ``OrchestrateRequest``. Here we
        validate the attachment: supported kind and size within the cap.
        """
        if file is None:
            return
        if file.kind is None:
            raise ValueError(
                f"unsupported file type {file.content_type!r} for {file.filename!r} "
                "— only images (png/jpg/webp/gif) and PDF"
            )
        if len(file.decode_bytes()) > settings.max_file_bytes:
            cap = settings.max_file_bytes // (1024 * 1024)
            raise ValueError(f"{file.filename!r} exceeds the {cap} MiB limit")

    def inject(self, args: dict, file: FilePayload | None) -> None:
        """Overwrite the tool's `file` field with the attached file (R3).

        The model is told to leave `file` empty; we fill it here so the raw payload is
        passed through to the sub-agent unchanged (as a plain dict over MCP/JSON).
        """
        if file is None:
            return
        payload = args.get("request", args)
        if isinstance(payload, dict):
            payload["file"] = file.model_dump()
