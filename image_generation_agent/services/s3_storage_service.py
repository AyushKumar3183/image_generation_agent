"""Upload generated images to AWS S3."""

from __future__ import annotations

import asyncio
import logging
import mimetypes
import time

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from image_generation_agent.utils.config import (
    AWS_ACCESS_KEY_ID,
    AWS_REGION,
    AWS_S3_BUCKET_NAME,
    AWS_SECRET_ACCESS_KEY,
    S3_KEY_PREFIX,
)

logger = logging.getLogger(__name__)


class S3StorageService:
    """Uploads image bytes to S3 and returns a public object URL."""

    def __init__(
        self,
        *,
        bucket: str | None = None,
        region: str | None = None,
        key_prefix: str | None = None,
    ) -> None:
        self._bucket = bucket or AWS_S3_BUCKET_NAME
        self._region = region or AWS_REGION
        self._key_prefix = (key_prefix or S3_KEY_PREFIX or "generated-images").strip("/")
        self._client = None
        self._folder_ready = False

    @property
    def is_configured(self) -> bool:
        return bool(
            self._bucket
            and self._region
            and AWS_ACCESS_KEY_ID
            and AWS_SECRET_ACCESS_KEY
        )

    @property
    def folder_path(self) -> str:
        return self._key_prefix

    @property
    def client(self):
        if self._client is None:
            session_kwargs: dict = {"region_name": self._region}
            if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
                session_kwargs["aws_access_key_id"] = AWS_ACCESS_KEY_ID
                session_kwargs["aws_secret_access_key"] = AWS_SECRET_ACCESS_KEY
            self._client = boto3.client("s3", **session_kwargs)
        return self._client

    @staticmethod
    def _extension_for_mime(mime_type: str) -> str:
        ext = mimetypes.guess_extension(mime_type or "image/png") or ".png"
        if ext == ".jpe":
            return ".jpg"
        return ext

    def _build_object_url(self, key: str) -> str:
        return f"https://{self._bucket}.s3.{self._region}.amazonaws.com/{key}"

    async def ensure_folder_exists(self) -> str:
        """Create the storage folder in S3 if it does not exist yet."""
        if not self.is_configured:
            raise RuntimeError(
                "S3 is not configured. Set AWS_S3_BUCKET_NAME, AWS_REGION, "
                "AWS_ACCESS_KEY_ID, and AWS_SECRET_ACCESS_KEY in .env"
            )

        if self._folder_ready:
            return self._key_prefix

        keep_key = f"{self._key_prefix}/.keep"

        def _ensure() -> None:
            existing = self.client.list_objects_v2(
                Bucket=self._bucket,
                Prefix=f"{self._key_prefix}/",
                MaxKeys=1,
            )
            if existing.get("KeyCount", 0) == 0:
                self.client.put_object(
                    Bucket=self._bucket,
                    Key=keep_key,
                    Body=b"",
                    ContentType="application/octet-stream",
                )
                logger.info(
                    "Created S3 folder s3://%s/%s/",
                    self._bucket,
                    self._key_prefix,
                )
            else:
                logger.info(
                    "S3 folder already exists s3://%s/%s/",
                    self._bucket,
                    self._key_prefix,
                )

        try:
            await asyncio.to_thread(_ensure)
        except (ClientError, BotoCoreError) as exc:
            logger.exception("Failed to ensure S3 folder %s", self._key_prefix)
            raise RuntimeError(f"Failed to create S3 folder: {exc}") from exc

        self._folder_ready = True
        return self._key_prefix

    async def upload_image(
        self,
        *,
        image_bytes: bytes,
        request_id: str,
        mime_type: str,
    ) -> str:
        if not self.is_configured:
            raise RuntimeError(
                "S3 is not configured. Set AWS_S3_BUCKET_NAME, AWS_REGION, "
                "AWS_ACCESS_KEY_ID, and AWS_SECRET_ACCESS_KEY in .env"
            )

        await self.ensure_folder_exists()

        ext = self._extension_for_mime(mime_type)
        key = f"{self._key_prefix}/{request_id}{ext}"
        size_bytes = len(image_bytes)

        logger.info(
            "[S3 Upload] Uploading to bucket=%s key=%s request_id=%s size_bytes=%s mime_type=%s",
            self._bucket,
            key,
            request_id,
            size_bytes,
            mime_type,
        )

        started_at = time.perf_counter()

        def _upload() -> None:
            self.client.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=image_bytes,
                ContentType=mime_type,
            )

        try:
            await asyncio.to_thread(_upload)
        except (ClientError, BotoCoreError) as exc:
            logger.exception(
                "[S3 Upload] Failed request_id=%s key=%s bucket=%s",
                request_id,
                key,
                self._bucket,
            )
            raise RuntimeError(f"S3 upload failed: {exc}") from exc

        elapsed_ms = (time.perf_counter() - started_at) * 1000
        url = self._build_object_url(key)
        logger.info(
            "[S3 Upload] Success request_id=%s key=%s url=%s duration_ms=%.0f",
            request_id,
            key,
            url,
            elapsed_ms,
        )
        return url
