"""The verdict contract — the whole API surface of this service (TASK R2, A3-5).

``Decision`` is two-valued. The third state, ``review``, is gone: the human in the
loop on the medical path is the doctor reading the answer, not a moderator clearing
a queue, so a clinical question is answered with a disclaimer rather than held.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

# The exact wording required by TASK R5. Rendered here and nowhere else: three call
# sites consume it, none of them re-spell it (PLAN D8).
PII_NOTICE_TEMPLATE = (
    "Note: the user's personal data ({types}) was not passed to the system, per policy."
)

# The medical disclaimer (TASK A3-5). English, per A7-1, like every other string the
# user reads; spelled here and nowhere else for the same reason the notice above is.
MEDICAL_DISCLAIMER = (
    "This information may be inaccurate. It is provided for reference only and "
    "does not replace a consultation with a doctor."
)

# The medical disclaimer (TASK A3-5). English, per A7-1, like every other string the
# user reads; spelled here and nowhere else for the same reason the notice above is.
MEDICAL_DISCLAIMER = (
    "This information may be inaccurate. It is provided for reference only and "
    "does not replace a consultation with a doctor."
)


class Direction(str, Enum):
    """Which side of the LLM the text is on."""

    INPUT = "input"
    OUTPUT = "output"


class Decision(str, Enum):
    ALLOWED = "allowed"
    BLOCKED = "blocked"


class Category(str, Enum):
    SEXUAL = "sexual"
    DRUGS = "drugs"
    INJECTION = "injection"


class Surface(str, Enum):
    """Where the text came from. Policy branches on it (TASK R2a/b/c, PLAN D4).

    It cannot be folded into ``source``: that is a free-text caller label, and a policy
    decision must not be taken on a string nobody validates.
    """

    PROMPT = "prompt"
    DOCUMENT = "document"
    TOOL_RESULT = "tool_result"


class Redaction(BaseModel):
    """One PII type that was found and replaced. Never carries the value (TASK R11)."""

    type: str = Field(..., description="PII entity type, e.g. 'PHONE_NUMBER'.")
    count: int = Field(..., ge=1, description="How many instances were replaced.")


class CheckRequest(BaseModel):
    text: str = Field(..., description="The text to check. May be a prompt, a document, or an answer.")
    direction: Direction = Field(default=Direction.INPUT)
    surface: Surface = Field(
        default=Surface.PROMPT,
        description="Where the text came from: a user prompt, a document, a tool result.",
    )
    source: str = Field(
        default="unknown",
        description="Enforcement point that called: 'orchestrator' | 'doc_analyzer'.",
    )
    thread_id: str | None = Field(default=None, description="Conversation thread, for review records.")
    # Types redacted on the way in, so the output pass can check they did not come back.
    known_pii_types: list[str] = Field(default_factory=list)


class Verdict(BaseModel):
    """What the caller acts on. ``text`` is always the text safe to use downstream."""

    decision: Decision = Decision.ALLOWED
    categories: list[Category] = Field(default_factory=list)
    scores: dict[str, float] = Field(default_factory=dict)
    text: str = Field(default="", description="Redacted text; identical to input when nothing matched.")
    redactions: list[Redaction] = Field(default_factory=list)
    notice: str | None = Field(default=None, description="TASK R5 notice, when PII was redacted.")
    reason: str | None = None
    system_note: str | None = Field(
        default=None,
        description="Line the caller inserts verbatim when `text` came back fenced (D17).",
    )
    latency_ms: int = 0

    @property
    def allowed(self) -> bool:
        """True only when the turn may proceed."""
        return self.decision is Decision.ALLOWED
