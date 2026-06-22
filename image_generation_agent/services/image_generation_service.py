"""Image generation service — all business logic lives here."""

from __future__ import annotations

import asyncio
import logging
import time
import uuid

from google.adk.tools.tool_context import ToolContext
from google.genai import types

from image_generation_agent.models.requests import (
    MAX_NUMBER_OF_IMAGES,
    ImageGenerationRequest,
)
from image_generation_agent.models.responses import (
    ImageGenerationError,
    ImageGenerationResponse,
    ImageGenerationSuccess,
)
from image_generation_agent.services.gemini_image_backend import GeminiImageBackend
from image_generation_agent.services.s3_storage_service import S3StorageService
from image_generation_agent.utils.config import IMAGE_GENERATION_MODEL
from image_generation_agent.utils.prompt_builder import build_generation_prompt
from image_generation_agent.utils.references import MAX_REFERENCE_IMAGES, normalize_references
from image_generation_agent.utils.resolution import normalize_resolution
from image_generation_agent.utils.retry import RetryConfig, with_retry
from image_generation_agent.utils.workflow import detect_workflow

logger = logging.getLogger(__name__)


class ImageGenerationService:
    """Orchestrates validation, workflow selection, backend calls, and retries."""

    def __init__(
        self,
        *,
        retry_config: RetryConfig | None = None,
        backend: GeminiImageBackend | None = None,
        storage: S3StorageService | None = None,
    ) -> None:
        self._retry_config = retry_config or RetryConfig()
        self._backend = backend or GeminiImageBackend()
        self._storage = storage or S3StorageService()

    def build_request(
        self,
        *,
        prompt: str,
        reference_images: list[str] | None,
        resolution: str,
        number_of_images: int = 1,
    ) -> tuple[ImageGenerationRequest | None, ImageGenerationError | None]:
        request_id = str(uuid.uuid4())

        if not prompt or not prompt.strip():
            return None, ImageGenerationError(
                error_code="EMPTY_PROMPT",
                message="A non-empty prompt is required for image generation.",
                retryable=False,
                request_id=request_id,
            )

        if number_of_images < 1 or number_of_images > MAX_NUMBER_OF_IMAGES:
            return None, ImageGenerationError(
                error_code="INVALID_NUMBER_OF_IMAGES",
                message=f"number_of_images must be between 1 and {MAX_NUMBER_OF_IMAGES}.",
                retryable=False,
                request_id=request_id,
            )

        refs, invalid_refs = normalize_references(
            reference_images,
            prompt=prompt,
            allow_prompt_fallback=True,
        )

        if invalid_refs:
            return None, ImageGenerationError(
                error_code="INVALID_REFERENCE_URL",
                message=f"Invalid reference image URL(s): {', '.join(invalid_refs)}",
                retryable=False,
                request_id=request_id,
            )

        if len(refs) > MAX_REFERENCE_IMAGES:
            return None, ImageGenerationError(
                error_code="TOO_MANY_REFERENCES",
                message=f"At most {MAX_REFERENCE_IMAGES} reference images are supported.",
                retryable=False,
                request_id=request_id,
            )

        workflow = detect_workflow(len(refs))

        return ImageGenerationRequest(
            prompt=build_generation_prompt(prompt),
            reference_images=refs,
            resolution=normalize_resolution(resolution),
            workflow=workflow,
            number_of_images=number_of_images,
        ), None

    async def generate(
        self,
        request: ImageGenerationRequest,
        *,
        tool_context: ToolContext | None = None,
    ) -> ImageGenerationResponse:
        request_id = str(uuid.uuid4())
        started_at = time.perf_counter()

        logger.info(
            "[Image Generation] Starting batch request_id=%s workflow=%s refs=%s resolution=%s count=%s",
            request_id,
            request.workflow.value,
            len(request.reference_images),
            request.resolution.value,
            request.number_of_images,
        )

        tasks = [
            self._generate_and_upload_single(
                request=request,
                request_id=f"{request_id}-{index + 1}",
                save_artifact=tool_context is not None and index == 0,
                tool_context=tool_context,
            )
            for index in range(request.number_of_images)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        image_urls: list[str] = []
        mime_type = "image/png"
        artifact_name: str | None = None

        for index, result in enumerate(results):
            if isinstance(result, Exception):
                logger.exception(
                    "Parallel generation failed request_id=%s index=%s",
                    request_id,
                    index + 1,
                )
                return ImageGenerationResponse(
                    result=ImageGenerationError(
                        error_code="GENERATION_FAILED",
                        message=str(result),
                        retryable=True,
                        request_id=request_id,
                    )
                )
            url, item_mime, item_artifact = result
            image_urls.append(url)
            mime_type = item_mime
            if item_artifact:
                artifact_name = item_artifact

        elapsed_ms = (time.perf_counter() - started_at) * 1000
        logger.info(
            "[Image Generation] Batch completed request_id=%s count=%s duration_ms=%.0f urls=%s",
            request_id,
            len(image_urls),
            elapsed_ms,
            image_urls,
        )

        return ImageGenerationResponse(
            result=ImageGenerationSuccess(
                image_urls=image_urls,
                mime_type=mime_type,
                resolution=request.resolution,
                workflow=request.workflow,
                reference_image_count=len(request.reference_images),
                number_of_images=len(image_urls),
                request_id=request_id,
                artifact_name=artifact_name,
                model=IMAGE_GENERATION_MODEL,
            )
        )

    async def _generate_and_upload_single(
        self,
        *,
        request: ImageGenerationRequest,
        request_id: str,
        save_artifact: bool,
        tool_context: ToolContext | None,
    ) -> tuple[str, str, str | None]:
        started_at = time.perf_counter()
        logger.info(
            "[Image Generation] Starting single image request_id=%s workflow=%s resolution=%s",
            request_id,
            request.workflow.value,
            request.resolution.value,
        )

        async def _call_backend() -> dict:
            return await self._invoke_backend(request, request_id=request_id)

        backend_result = await with_retry(
            _call_backend,
            should_retry=lambda r: r.get("retryable", False),
            config=self._retry_config,
        )

        if backend_result.get("status") != "success":
            logger.error(
                "[Image Generation] Failed request_id=%s message=%s",
                request_id,
                backend_result.get("message", "Image generation failed."),
            )
            raise RuntimeError(
                backend_result.get("message", "Image generation failed.")
            )

        image_bytes = backend_result.get("image_bytes")
        mime_type = backend_result.get("mime_type", "image/png")
        if not image_bytes:
            logger.error("[Image Generation] No image bytes returned request_id=%s", request_id)
            raise RuntimeError("No image bytes returned from backend.")

        generation_ms = (time.perf_counter() - started_at) * 1000
        logger.info(
            "[Image Generation] Gemini returned image request_id=%s size_bytes=%s mime_type=%s duration_ms=%.0f",
            request_id,
            len(image_bytes),
            mime_type,
            generation_ms,
        )

        artifact_name: str | None = None
        if save_artifact and tool_context:
            artifact_name = f"generated_{request_id}.png"
            await tool_context.save_artifact(
                artifact_name,
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            )

        upload_started_at = time.perf_counter()
        logger.info("[S3 Upload] Starting upload request_id=%s size_bytes=%s", request_id, len(image_bytes))
        image_url = await self._storage.upload_image(
            image_bytes=image_bytes,
            request_id=request_id,
            mime_type=mime_type,
        )
        upload_ms = (time.perf_counter() - upload_started_at) * 1000
        total_ms = (time.perf_counter() - started_at) * 1000
        logger.info(
            "[S3 Upload] Finished request_id=%s url=%s upload_ms=%.0f total_ms=%.0f",
            request_id,
            image_url,
            upload_ms,
            total_ms,
        )
        return image_url, mime_type, artifact_name

    async def generate_from_params(
        self,
        *,
        prompt: str,
        reference_images: list[str] | None = None,
        resolution: str = "1K",
        number_of_images: int = 1,
        tool_context: ToolContext | None = None,
    ) -> ImageGenerationResponse:
        """Build, validate, orchestrate workflow, and run generation."""
        request, error = self.build_request(
            prompt=prompt,
            reference_images=reference_images,
            resolution=resolution,
            number_of_images=number_of_images,
        )
        if error:
            return ImageGenerationResponse(result=error)
        assert request is not None
        return await self.generate(request, tool_context=tool_context)

    async def _invoke_backend(
        self,
        request: ImageGenerationRequest,
        *,
        request_id: str,
    ) -> dict:
        return await self._backend.generate(request, request_id=request_id)
