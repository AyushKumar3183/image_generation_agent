"""ADK function tool — thin adapter over ImageGenerationService."""

from __future__ import annotations

from typing import Literal

from google.adk.tools.tool_context import ToolContext

from image_generation_agent.services.image_generation_service import ImageGenerationService

_service = ImageGenerationService()


async def generate_image_tool(
    prompt: str,
    reference_images: list[str] | None = None,
    resolution: Literal["1K", "2K", "4K"] = "1K",
    number_of_images: int = 1,
    tool_context: ToolContext | None = None,
) -> dict:
    """Generate an image from a text prompt, optionally guided by reference images.

    Always use this tool for any image generation request. Never invent image URLs.
    Workflow (text-to-image / image-to-image / multi-image) is selected automatically
    from the number of reference_images. Do not pass a generation mode.

    Args:
        prompt: Verbatim user creative intent. Do not rewrite or omit details.
        reference_images: Optional HTTP/HTTPS image URLs. 0 = text-to-image,
            1 = image-to-image, 2+ = multi-image generation.
        resolution: Output resolution — 1K, 2K, or 4K. Default 1K.
        number_of_images: How many images to generate (1-4). Default 1.
        tool_context: Injected by ADK.

    Returns:
        Dict with status success or error. On success includes image_urls from S3.
    """
    response = await _service.generate_from_params(
        prompt=prompt,
        reference_images=reference_images,
        resolution=resolution,
        number_of_images=number_of_images,
        tool_context=tool_context,
    )
    return response.to_tool_dict()
