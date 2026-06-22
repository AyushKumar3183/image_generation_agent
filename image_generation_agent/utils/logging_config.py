"""Application logging configuration."""

from __future__ import annotations

import logging
import warnings

from image_generation_agent.utils.env import env


def configure_logging() -> None:
    """Configure root logging — warnings and errors only by default."""
    warnings.filterwarnings(
        "ignore",
        message=".*EXPERIMENTAL.*",
        category=UserWarning,
        module=r"google\.adk\..*",
    )

    level_name = (env("LOG_LEVEL") or "WARNING").upper()
    level = getattr(logging, level_name, logging.WARNING)

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,
    )

    for noisy_logger in (
        "botocore",
        "boto3",
        "urllib3",
        "httpx",
        "httpcore",
        "google_adk",
        "google.genai",
        "uvicorn.access",
    ):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)
