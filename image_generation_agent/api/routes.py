"""Image generation HTTP routes."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Body, Depends, status
from fastapi.responses import JSONResponse

from image_generation_agent.api.dependencies import get_image_generation_service
from image_generation_agent.api.schemas import (
    DEFAULT_REQUEST_EXAMPLE,
    GenerateImageRequest,
    HealthResponse,
)
from image_generation_agent.models.responses import ImageGenerationError, ImageGenerationSuccess
from image_generation_agent.services.image_generation_service import ImageGenerationService

router = APIRouter(tags=["images"])
logger = logging.getLogger(__name__)

_CLIENT_ERROR_CODES = frozenset({
    "EMPTY_PROMPT",
    "INVALID_REFERENCE_URL",
    "TOO_MANY_REFERENCES",
    "INVALID_NUMBER_OF_IMAGES",
})


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse()


@router.post(
    "/v1/images/generate",
    summary="Generate an image",
    description=(
        "Generate or modify images from a prompt. "
        "Workflow is selected automatically from reference_images count: "
        "0 → text-to-image, 1 → image-to-image, 2+ → multi-image generation. "
        "Do not send generation_mode."
    ),
)
async def generate_image(
    body: GenerateImageRequest = Body(
        ...,
        openapi_examples={
            "default": {
                "summary": "Default — all fields",
                "value": DEFAULT_REQUEST_EXAMPLE,
            },
            "text_to_image": {
                "summary": "Text-to-image",
                "value": {
                    "prompt": "Generate a luxury evening gown",
                    "reference_images": [],
                    "resolution": "1K",
                    "number_of_images": 1,
                },
            },
            "image_to_image": {
                "summary": "Image-to-image",
                "value": {
                    "prompt": "Make this dress black",
                    "reference_images": ["https://cdn.example.com/dress.jpg"],
                    "resolution": "1K",
                    "number_of_images": 1,
                },
            },
            "multi_output": {
                "summary": "Generate 4 variations",
                "value": {
                    "prompt": "Generate a luxury evening gown",
                    "reference_images": [],
                    "resolution": "2K",
                    "number_of_images": 4,
                },
            },
            "multi_image": {
                "summary": "Multi-image generation",
                "value": {
                    "prompt": "Create a new outfit using these references",
                    "reference_images": [
                        "https://cdn.example.com/top.jpg",
                        "https://cdn.example.com/skirt.jpg",
                    ],
                    "resolution": "4K",
                },
            },
        },
    ),
    service: ImageGenerationService = Depends(get_image_generation_service),
) -> JSONResponse:
    logger.info(
        "[API] Image generation request prompt_len=%s refs=%s resolution=%s number_of_images=%s",
        len(body.prompt),
        len(body.reference_images),
        body.resolution.value,
        body.number_of_images,
    )
    response = await service.generate_from_params(
        prompt=body.prompt,
        reference_images=body.reference_images or None,
        resolution=body.resolution.value,
        number_of_images=body.number_of_images,
    )

    payload = response.to_tool_dict()

    if isinstance(response.result, ImageGenerationSuccess):
        logger.info(
            "[API] Image generation succeeded request_id=%s count=%s",
            response.result.request_id,
            response.result.number_of_images,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=payload)

    assert isinstance(response.result, ImageGenerationError)
    error = response.result
    logger.warning(
        "[API] Image generation failed error_code=%s request_id=%s message=%s",
        error.error_code,
        error.request_id,
        error.message,
    )
    if error.error_code in _CLIENT_ERROR_CODES:
        http_status = status.HTTP_400_BAD_REQUEST
    elif error.retryable:
        http_status = status.HTTP_503_SERVICE_UNAVAILABLE
    else:
        http_status = status.HTTP_502_BAD_GATEWAY

    return JSONResponse(status_code=http_status, content=payload)
