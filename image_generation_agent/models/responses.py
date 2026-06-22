"""Response models for image generation."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from image_generation_agent.models.requests import Resolution, Workflow


class ImageGenerationSuccess(BaseModel):
    status: Literal["success"] = "success"
    image_urls: list[str] = Field(default_factory=list)
    mime_type: str = "image/png"
    resolution: Resolution
    workflow: Workflow
    reference_image_count: int = 0
    number_of_images: int = 1
    request_id: str
    artifact_name: str | None = None
    model: str | None = None

    @model_validator(mode="after")
    def validate_image_urls(self) -> ImageGenerationSuccess:
        if not self.image_urls:
            raise ValueError("success response requires at least one image_url")
        return self


class ImageGenerationError(BaseModel):
    status: Literal["error"] = "error"
    error_code: str
    message: str
    retryable: bool = False
    request_id: str | None = None


class ImageGenerationResponse(BaseModel):
    """Union wrapper serialized to dict for ADK tool return."""

    result: ImageGenerationSuccess | ImageGenerationError

    def to_tool_dict(self) -> dict:
        return self.result.model_dump(exclude_none=True)
