"""Resolution extraction and normalization."""

from __future__ import annotations

import re

from image_generation_agent.models.requests import Resolution

_RESOLUTION_ALIASES: dict[str, Resolution] = {
    "1K": Resolution.K1,
    "2K": Resolution.K2,
    "4K": Resolution.K4,
    "1024": Resolution.K1,
    "2048": Resolution.K2,
    "4096": Resolution.K4,
}

_RESOLUTION_PATTERNS: list[tuple[re.Pattern[str], Resolution]] = [
    (re.compile(r"\b4\s*k\b|\b4096\b|ultra\s*hd|highest", re.I), Resolution.K4),
    (re.compile(r"\b2\s*k\b|\b2048\b|high\s*res(olution)?", re.I), Resolution.K2),
    (re.compile(r"\b1\s*k\b|\b1024\b", re.I), Resolution.K1),
]


def normalize_resolution(value: str | None, *, default: Resolution = Resolution.K1) -> Resolution:
    if not value:
        return default
    key = value.strip().upper().replace(" ", "")
    return _RESOLUTION_ALIASES.get(key, default)


def extract_resolution(text: str) -> Resolution:
    for pattern, resolution in _RESOLUTION_PATTERNS:
        if pattern.search(text):
            return resolution
    return Resolution.K1
