"""Image generation HTTP routes."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Body, Depends, status
from fastapi.responses import JSONResponse

from image_generation_agent.agent_runner import ImageGenerationAgentRunner
from image_generation_agent.api.dependencies import get_agent_runner
from image_generation_agent.api.schemas import (
    DEFAULT_REQUEST_EXAMPLE,
    GenerateImageRequest,
    HealthResponse,
)

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
        "Generate or modify images from a prompt via root_agent. "
        "Flow: Agent → generate_image_tool → service. "
        "Workflow is selected automatically from reference_images count."
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
    agent_runner: ImageGenerationAgentRunner = Depends(get_agent_runner),
) -> JSONResponse:
    payload = await agent_runner.generate(
        prompt=body.prompt,
        reference_images=body.reference_images,
        resolution=body.resolution.value,
        number_of_images=body.number_of_images,
    )

    if payload.get("status") == "success":
        return JSONResponse(status_code=status.HTTP_200_OK, content=payload)

    error_code = payload.get("error_code", "GENERATION_FAILED")
    logger.warning(
        "Image generation failed error_code=%s request_id=%s message=%s",
        error_code,
        payload.get("request_id"),
        payload.get("message"),
    )

    if error_code in _CLIENT_ERROR_CODES:
        http_status = status.HTTP_400_BAD_REQUEST
    elif payload.get("retryable"):
        http_status = status.HTTP_503_SERVICE_UNAVAILABLE
    else:
        http_status = status.HTTP_502_BAD_GATEWAY

    return JSONResponse(status_code=http_status, content=payload)
