"""Unit tests for image generation tool and service."""

import pytest

from image_generation_agent.models.requests import Workflow
from image_generation_agent.services.image_generation_service import ImageGenerationService
from image_generation_agent.tools.generate_image_tool import generate_image_tool


@pytest.fixture
def service() -> ImageGenerationService:
    return ImageGenerationService()


@pytest.mark.asyncio
async def test_text_to_image_success(mock_backend_success, mock_s3_upload):
    result = await generate_image_tool(
        prompt="Sunset over Tokyo skyline, cinematic",
        resolution="4K",
        tool_context=None,  # type: ignore[arg-type]
    )
    assert result["status"] == "success"
    assert result["resolution"] == "4K"
    assert result["workflow"] == "text_to_image"
    assert len(result["image_urls"]) == 1
    assert result["number_of_images"] == 1
    assert "image_base64" not in result
    mock_s3_upload.assert_awaited_once()


@pytest.mark.asyncio
async def test_image_to_image_single_reference(mock_backend_success, mock_s3_upload):
    result = await generate_image_tool(
        prompt="Make this dress black",
        reference_images=["https://cdn.example.com/dress.jpg"],
        tool_context=None,  # type: ignore[arg-type]
    )
    assert result["status"] == "success"
    assert result["workflow"] == "image_to_image"
    assert result["reference_image_count"] == 1
    assert len(result["image_urls"]) == 1


@pytest.mark.asyncio
async def test_multi_image_generation(mock_backend_success, mock_s3_upload):
    result = await generate_image_tool(
        prompt="Create a new outfit using these references",
        reference_images=[
            "https://cdn.example.com/top.jpg",
            "https://cdn.example.com/skirt.jpg",
            "https://cdn.example.com/jacket.jpg",
        ],
        resolution="4K",
        tool_context=None,  # type: ignore[arg-type]
    )
    assert result["status"] == "success"
    assert result["workflow"] == "multi_image_generation"
    assert result["reference_image_count"] == 3


@pytest.mark.asyncio
async def test_empty_prompt_returns_error():
    result = await generate_image_tool(
        prompt="   ",
        tool_context=None,  # type: ignore[arg-type]
    )
    assert result["status"] == "error"
    assert result["error_code"] == "EMPTY_PROMPT"


@pytest.mark.asyncio
async def test_invalid_reference_placeholder_ignored(mock_backend_success, mock_s3_upload):
    result = await generate_image_tool(
        prompt="A red sports car",
        reference_images=["string"],
        tool_context=None,  # type: ignore[arg-type]
    )
    assert result["status"] == "success"
    assert result["workflow"] == "text_to_image"


@pytest.mark.asyncio
async def test_malformed_http_url_returns_error():
    result = await generate_image_tool(
        prompt="Edit this image",
        reference_images=["https://"],
        tool_context=None,  # type: ignore[arg-type]
    )
    assert result["status"] == "error"
    assert result["error_code"] == "INVALID_REFERENCE_URL"


def test_build_request_text_to_image(service: ImageGenerationService):
    request, error = service.build_request(
        prompt="Generate a luxury evening gown",
        reference_images=None,
        resolution="1K",
    )
    assert error is None
    assert request is not None
    assert request.workflow == Workflow.TEXT_TO_IMAGE


def test_build_request_image_to_image(service: ImageGenerationService):
    request, error = service.build_request(
        prompt="Make this dress black",
        reference_images=["https://cdn.example.com/dress.jpg"],
        resolution="1K",
    )
    assert error is None
    assert request is not None
    assert request.workflow == Workflow.IMAGE_TO_IMAGE


def test_build_request_multi_image(service: ImageGenerationService):
    request, error = service.build_request(
        prompt="Combine these references",
        reference_images=[
            "https://cdn.example.com/a.jpg",
            "https://cdn.example.com/b.jpg",
        ],
        resolution="4K",
    )
    assert error is None
    assert request is not None
    assert request.workflow == Workflow.MULTI_IMAGE_GENERATION


@pytest.mark.asyncio
async def test_multiple_output_images_parallel(mock_backend_success, mock_s3_upload):
    mock_s3_upload.side_effect = [
        f"https://vrozart-fashion-app.s3.ap-south-1.amazonaws.com/generated-images/test-{i}.jpg"
        for i in range(4)
    ]
    result = await generate_image_tool(
        prompt="Generate a luxury evening gown",
        number_of_images=4,
        tool_context=None,  # type: ignore[arg-type]
    )
    assert result["status"] == "success"
    assert result["number_of_images"] == 4
    assert len(result["image_urls"]) == 4
    assert mock_backend_success.await_count == 4
    assert mock_s3_upload.await_count == 4


@pytest.mark.asyncio
async def test_invalid_number_of_images(service: ImageGenerationService):
    _, error = service.build_request(
        prompt="Generate a luxury evening gown",
        reference_images=None,
        resolution="1K",
        number_of_images=5,
    )
    assert error is not None
    assert error.error_code == "INVALID_NUMBER_OF_IMAGES"
