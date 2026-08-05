"""The single REST response envelope shared by every microservice.

Wire shape (matches the frontend contract exactly):

    { "status": "Success" | "Failed", "data"?: T, "error_text"?: string }

Every router returns an ``ApiResponse[T]``. Success carries ``data``; failure
carries ``error_text``. This is the fail-soft boundary: errors are represented
as data, never as an unstructured HTTP 500.
"""

from __future__ import annotations

from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ResponseStatus(str, Enum):
    """Literal status values on the wire.

    NOTE: the original spec wrote ``"Faild"``; corrected to ``"Failed"`` by the
    Engineer (recorded in TASK.md R4) so both ends agree on the literal.
    """

    SUCCESS = "Success"
    FAILED = "Failed"


class ApiResponse(BaseModel, Generic[T]):
    """Uniform response envelope for all REST endpoints."""

    status: ResponseStatus = Field(..., description="Success or Failed.")
    data: T | None = Field(default=None, description="Payload present on success.")
    error_text: str | None = Field(
        default=None, description="Human-readable error present on failure."
    )
    error_code: str | None = Field(
        default=None,
        description="Machine-readable failure kind (e.g. 'turn_timeout'). Optional and "
        "additive: clients branch on this instead of parsing error_text.",
    )

    @classmethod
    def ok(cls, data: T) -> "ApiResponse[T]":
        """Build a successful envelope."""
        return cls(
            status=ResponseStatus.SUCCESS, data=data, error_text=None, error_code=None
        )

    @classmethod
    def fail(cls, error_text: str, error_code: str | None = None) -> "ApiResponse[T]":
        """Build a failed envelope (no payload)."""
        return cls(
            status=ResponseStatus.FAILED,
            data=None,
            error_text=error_text,
            error_code=error_code,
        )
