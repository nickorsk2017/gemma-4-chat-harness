"""Domain models for doc_analyzer."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DocAnalysis(BaseModel):
    """The model's answer to the user's instruction about the document."""

    filename: str = Field(..., description="The analyzed document's file name.")
    answer: str = Field(..., description="The model's response to the prompt.")
