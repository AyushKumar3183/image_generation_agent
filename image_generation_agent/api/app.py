"""FastAPI application factory."""

from __future__ import annotations

import logging

from fastapi import FastAPI

from image_generation_agent.api.dependencies import get_s3_storage_service
from image_generation_agent.api.routes import router
from image_generation_agent.utils.config import AWS_S3_BUCKET_NAME, S3_KEY_PREFIX
from image_generation_agent.utils.env import load_env
from image_generation_agent.utils.logging_config import configure_logging

logger = logging.getLogger(__name__)

load_env()
configure_logging()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Image Generation Agent API",
        description="HTTP API for the image generation service.",
        version="1.0.0",
    )
    app.include_router(router)

    @app.on_event("startup")
    async def init_s3_storage_folder() -> None:
        storage = get_s3_storage_service()
        if not storage.is_configured:
            logger.warning(
                "S3 credentials or bucket not configured — image uploads will fail until .env is set."
            )
            return
        folder = await storage.ensure_folder_exists()
        logger.info(
            "S3 ready bucket=%s folder=%s",
            AWS_S3_BUCKET_NAME,
            folder or S3_KEY_PREFIX,
        )

    return app


app = create_app()
