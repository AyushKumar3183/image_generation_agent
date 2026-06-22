"""Gemini image generation backend using gemini-3.1-flash-image."""

from __future__ import annotations

import logging
import time

from google import genai
from google.genai import types

from image_generation_agent.models.requests import ImageGenerationRequest
from image_generation_agent.utils.config import IMAGE_GENERATION_MODEL

logger = logging.getLogger(__name__)


class GeminiImageBackend:
    """Calls Gemini native image generation via generate_content."""

    def __init__(self, *, model: str = IMAGE_GENERATION_MODEL) -> None:
        self._model = model
        self._client: genai.Client | None = None

    @property
    def client(self) -> genai.Client:
        if self._client is None:
            self._client = genai.Client()
        return self._client

    async def generate(
        self,
        request: ImageGenerationRequest,
        *,
        request_id: str,
    ) -> dict:
        contents: list[types.Part] = [types.Part.from_text(text=request.prompt)]

        for url in request.reference_images:
            contents.append(types.Part.from_uri(file_uri=url))

        config = types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(
                image_size=request.resolution.value,
            ),
        )

        started_at = time.perf_counter()
        logger.info(
            "[Image Generation] Calling Gemini request_id=%s model=%s workflow=%s resolution=%s refs=%s",
            request_id,
            self._model,
            request.workflow.value,
            request.resolution.value,
            len(request.reference_images),
        )

        try:
            response = await self.client.aio.models.generate_content(
                model=self._model,
                contents=contents,
                config=config,
            )
        except Exception as exc:
            logger.exception(
                "[Image Generation] Gemini API error request_id=%s model=%s workflow=%s",
                request_id,
                self._model,
                request.workflow.value,
            )
            return {
                "status": "error",
                "error_code": "GEMINI_API_ERROR",
                "message": str(exc),
                "retryable": True,
            }

        elapsed_ms = (time.perf_counter() - started_at) * 1000

        for part in response.parts or []:
            if part.inline_data and part.inline_data.data:
                mime_type = part.inline_data.mime_type or "image/png"
                logger.info(
                    "[Image Generation] Gemini success request_id=%s model=%s size_bytes=%s mime_type=%s duration_ms=%.0f",
                    request_id,
                    self._model,
                    len(part.inline_data.data),
                    mime_type,
                    elapsed_ms,
                )
                return {
                    "status": "success",
                    "image_bytes": part.inline_data.data,
                    "mime_type": mime_type,
                }

        logger.warning(
            "[Image Generation] Gemini returned no image request_id=%s model=%s duration_ms=%.0f",
            request_id,
            self._model,
            elapsed_ms,
        )

        return {
            "status": "error",
            "error_code": "NO_IMAGE_OUTPUT",
            "message": "Model did not return an image. The prompt may have been blocked or invalid.",
            "retryable": False,
        }
