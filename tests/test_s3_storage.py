"""S3 storage service tests."""

from unittest.mock import MagicMock, patch

import pytest

from image_generation_agent.services.s3_storage_service import S3StorageService


@pytest.fixture
def storage():
    with patch("image_generation_agent.services.s3_storage_service.AWS_S3_BUCKET_NAME", "test-bucket"), \
         patch("image_generation_agent.services.s3_storage_service.AWS_REGION", "ap-south-1"), \
         patch("image_generation_agent.services.s3_storage_service.AWS_ACCESS_KEY_ID", "key"), \
         patch("image_generation_agent.services.s3_storage_service.AWS_SECRET_ACCESS_KEY", "secret"), \
         patch("image_generation_agent.services.s3_storage_service.S3_KEY_PREFIX", "generated-images"):
        yield S3StorageService()


@pytest.mark.asyncio
async def test_ensure_folder_creates_keep_file(storage: S3StorageService):
    mock_client = MagicMock()
    mock_client.list_objects_v2.return_value = {"KeyCount": 0}
    storage._client = mock_client

    folder = await storage.ensure_folder_exists()

    assert folder == "generated-images"
    mock_client.put_object.assert_called_once()
    assert mock_client.put_object.call_args.kwargs["Key"] == "generated-images/.keep"


@pytest.mark.asyncio
async def test_ensure_folder_skips_if_exists(storage: S3StorageService):
    mock_client = MagicMock()
    mock_client.list_objects_v2.return_value = {"KeyCount": 1}
    storage._client = mock_client

    await storage.ensure_folder_exists()

    mock_client.put_object.assert_not_called()


@pytest.mark.asyncio
async def test_upload_uses_folder_prefix(storage: S3StorageService):
    mock_client = MagicMock()
    mock_client.list_objects_v2.return_value = {"KeyCount": 1}
    storage._client = mock_client

    url = await storage.upload_image(
        image_bytes=b"data",
        request_id="abc-123",
        mime_type="image/jpeg",
    )

    assert "generated-images/abc-123.jpg" in url
    put_key = mock_client.put_object.call_args.kwargs["Key"]
    assert put_key == "generated-images/abc-123.jpg"
