"""Shared test fixtures."""

from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture
def mock_backend_success():
    with patch(
        "image_generation_agent.services.gemini_image_backend.GeminiImageBackend.generate",
        new_callable=AsyncMock,
    ) as mock:
        mock.return_value = {
            "status": "success",
            "image_bytes": b"fake-image-bytes",
            "mime_type": "image/jpeg",
        }
        yield mock


@pytest.fixture
def mock_s3_upload():
    with patch(
        "image_generation_agent.services.s3_storage_service.S3StorageService.upload_image",
        new_callable=AsyncMock,
    ) as mock:
        mock.return_value = (
            "https://vrozart-fashion-app.s3.ap-south-1.amazonaws.com/generated-images/test-id.jpg"
        )
        yield mock
