"""Uvicorn entry point: uvicorn main:app --reload"""

from image_generation_agent.api.app import app

__all__ = ["app"]
