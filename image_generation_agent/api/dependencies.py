"""FastAPI dependencies."""

from __future__ import annotations

from functools import lru_cache

from image_generation_agent.agent_runner import ImageGenerationAgentRunner
from image_generation_agent.services.s3_storage_service import S3StorageService


@lru_cache
def get_s3_storage_service() -> S3StorageService:
    return S3StorageService()


@lru_cache
def get_agent_runner() -> ImageGenerationAgentRunner:
    return ImageGenerationAgentRunner()
