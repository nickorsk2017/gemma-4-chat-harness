"""Domain models for image_analyzer."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ImageAnalysis(BaseModel):
    """The model's answer to the user's instruction about the image."""

    filename: str = Field(..., description="The analyzed image's file name.")
    answer: str = Field(..., description="The model's response to the prompt.")
