"""API request/response schemas."""

from __future__ import annotations

import logging

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from image_generation_agent.models.requests import Resolution
from image_generation_agent.utils.references import should_ignore_reference_value

logger = logging.getLogger(__name__)

DEFAULT_REQUEST_EXAMPLE = {
    "prompt": "Generate a luxury evening gown",
    "reference_images": [],
    "resolution": "1K",
    "number_of_images": 1,
}


class GenerateImageRequest(BaseModel):
    """Public API request — workflow is inferred from reference_images count."""

    model_config = ConfigDict(
        extra="ignore",
        json_schema_extra={"example": DEFAULT_REQUEST_EXAMPLE},
    )

    prompt: str = Field(
        ...,
        min_length=1,
        description="Natural language image generation instruction.",
        json_schema_extra={"example": "Generate a luxury evening gown"},
    )
    reference_images: list[str] = Field(
        default_factory=list,
        description=(
            "Optional reference image URLs (HTTP/HTTPS). "
            "0 images = text-to-image, 1 = image-to-image, 2+ = multi-image."
        ),
        json_schema_extra={"example": []},
    )
    resolution: Resolution = Field(
        default=Resolution.K1,
        description='Output resolution: "1K", "2K", or "4K". Defaults to "1K".',
        json_schema_extra={"example": "1K"},
    )
    number_of_images: int = Field(
        default=1,
        ge=1,
        le=4,
        description="Number of images to generate (1-4). Defaults to 1.",
        json_schema_extra={"example": 1},
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_fields(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data

        normalized = dict(data)

        if "reference_image_urls" in normalized and "reference_images" not in normalized:
            logger.warning(
                "Deprecated field 'reference_image_urls' received; use 'reference_images' instead."
            )
            normalized["reference_images"] = normalized.pop("reference_image_urls")

        if normalized.get("generation_mode") is not None:
            logger.warning(
                "Deprecated field 'generation_mode'=%r ignored; workflow is auto-detected.",
                normalized.get("generation_mode"),
            )
            normalized.pop("generation_mode", None)

        return normalized

    @field_validator("reference_images", mode="before")
    @classmethod
    def clean_reference_images(cls, value: object) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            value = [value]
        if not isinstance(value, list):
            return []
        return [
            url.strip()
            for url in value
            if isinstance(url, str) and not should_ignore_reference_value(url)
        ]

    @field_validator("prompt")
    @classmethod
    def strip_prompt(cls, value: str) -> str:
        return value.strip()


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "image_generation_agent"
