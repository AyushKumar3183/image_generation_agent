"""Retry utilities for transient backend failures."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass(frozen=True)
class RetryConfig:
    max_retries: int = 2
    base_delay_seconds: float = 1.5


async def with_retry(
    operation: Callable[[], Awaitable[T]],
    *,
    should_retry: Callable[[T], bool],
    config: RetryConfig | None = None,
) -> T:
    cfg = config or RetryConfig()
    last_result: T | None = None

    for attempt in range(1, cfg.max_retries + 2):
        last_result = await operation()
        if not should_retry(last_result):
            return last_result
        if attempt <= cfg.max_retries:
            delay = cfg.base_delay_seconds * attempt
            logger.warning("Retrying operation (attempt %s) after %.1fs", attempt, delay)
            await asyncio.sleep(delay)

    assert last_result is not None
    return last_result
