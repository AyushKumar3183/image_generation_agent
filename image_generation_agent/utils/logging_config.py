"""Application logging configuration."""

from __future__ import annotations

import logging

from image_generation_agent.utils.env import env


def configure_logging() -> None:
    """Configure root logging so service logs appear in the console."""
    level_name = (env("LOG_LEVEL") or "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,
    )

    for noisy_logger in ("botocore", "boto3", "urllib3", "httpx", "httpcore"):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)
