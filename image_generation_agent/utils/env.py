"""Environment configuration."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


def load_env() -> None:
    if ENV_FILE.is_file():
        load_dotenv(ENV_FILE, override=False)


def env(name: str, default: str | None = None) -> str | None:
    """Read env var and strip surrounding quotes/whitespace."""
    value = os.getenv(name, default)
    if value is None:
        return None
    return value.strip().strip('"').strip("'")


load_env()


def get_google_api_key() -> str | None:
    return env("GOOGLE_API_KEY") or env("GEMINI_API_KEY")
