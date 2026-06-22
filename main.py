"""Uvicorn entry point: uvicorn main:app --reload"""

from image_generation_agent.utils.env import load_env
from image_generation_agent.utils.logging_config import configure_logging

load_env()
configure_logging()

from image_generation_agent.api.app import app

__all__ = ["app"]
