"""Build the final prompt sent to the image generation model."""

from __future__ import annotations

from image_generation_agent.prompts.fashion_quality_rules import FASHION_QUALITY_RULES


def build_generation_prompt(user_prompt: str) -> str:
    """Combine verbatim user intent with mandatory fashion quality rules."""
    cleaned = user_prompt.strip()
    return (
        f"USER REQUEST:\n{cleaned}\n\n"
        f"{FASHION_QUALITY_RULES}"
    )
