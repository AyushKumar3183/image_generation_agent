"""Request models for image generation."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class Resolution(str, Enum):
    K1 = "1K"
    K2 = "2K"
    K4 = "4K"


class Workflow(str, Enum):
    TEXT_TO_IMAGE = "text_to_image"
    IMAGE_TO_IMAGE = "image_to_image"
    MULTI_IMAGE_GENERATION = "multi_image_generation"


MAX_NUMBER_OF_IMAGES = 4


class ImageGenerationRequest(BaseModel):
    """Validated internal request after orchestration."""

    prompt: str = Field(..., min_length=1, description="Verbatim user creative intent.")
    reference_images: list[str] = Field(default_factory=list)
    resolution: Resolution = Resolution.K1
    workflow: Workflow = Workflow.TEXT_TO_IMAGE
    number_of_images: int = Field(default=1, ge=1, le=MAX_NUMBER_OF_IMAGES)

    @field_validator("prompt")
    @classmethod
    def strip_prompt(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("prompt must not be empty")
        return stripped
