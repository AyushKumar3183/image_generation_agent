"""Application configuration."""

from __future__ import annotations

import os

from image_generation_agent.utils.env import env


IMAGE_GENERATION_MODEL = "gemini-3.1-flash-image"

AWS_S3_BUCKET_NAME = env("AWS_S3_BUCKET_NAME")
AWS_REGION = env("AWS_REGION", "ap-south-1")
AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
S3_KEY_PREFIX = env("S3_KEY_PREFIX", "generated-images")
