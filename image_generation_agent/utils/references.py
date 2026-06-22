"""Reference image URL handling."""

from __future__ import annotations

import re
from urllib.parse import urlparse

MAX_REFERENCE_IMAGES = 10
_URL_PATTERN = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)

# Swagger / OpenAPI default placeholder values — treat as "not provided".
_IGNORED_REFERENCE_PLACEHOLDERS = frozenset({
    "string",
    "url",
    "example",
    "example.com",
    "https://example.com",
    "http://example.com",
})


def is_valid_image_url(url: str) -> bool:
    parsed = urlparse(url.strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def looks_like_url_attempt(url: str) -> bool:
    return url.strip().lower().startswith(("http://", "https://"))


def should_ignore_reference_value(url: str) -> bool:
    normalized = url.strip().lower()
    if not normalized:
        return True
    return normalized in _IGNORED_REFERENCE_PLACEHOLDERS


def extract_urls_from_text(text: str) -> list[str]:
    return _URL_PATTERN.findall(text or "")


def normalize_references(
    urls: list[str] | None,
    *,
    prompt: str = "",
    allow_prompt_fallback: bool = False,
) -> tuple[list[str], list[str]]:
    """Return (valid_urls, invalid_urls).

    Invalid placeholders (e.g. Swagger default ``\"string\"``) are silently skipped.
    Only values that look like http(s) URL attempts but fail validation are reported.
    """
    raw: list[str]
    if urls is None:
        raw = []
    elif isinstance(urls, str):
        raw = [urls]
    else:
        raw = list(urls)

    seen: set[str] = set()
    valid: list[str] = []
    invalid: list[str] = []

    for url in raw:
        url = url.strip()
        if should_ignore_reference_value(url):
            continue
        if url in seen:
            continue
        seen.add(url)
        if is_valid_image_url(url):
            valid.append(url)
        elif looks_like_url_attempt(url):
            invalid.append(url)

    if allow_prompt_fallback and not valid:
        for url in extract_urls_from_text(prompt):
            if url not in seen and is_valid_image_url(url):
                seen.add(url)
                valid.append(url)

    return valid[:MAX_REFERENCE_IMAGES], invalid
