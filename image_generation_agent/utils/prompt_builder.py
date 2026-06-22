"""Build the final prompt sent to the image generation model."""

from __future__ import annotations

from image_generation_agent.prompts.fashion_quality_rules import FASHION_QUALITY_RULES
from image_generation_agent.prompts.multi_image_variation_rules import (
    format_multi_image_variation,
)
from image_generation_agent.prompts.studio_composition_rules import STUDIO_COMPOSITION_RULES


def build_generation_prompt(
    user_prompt: str,
    *,
    image_index: int | None = None,
    total_images: int = 1,
) -> str:
    """Combine user intent, fashion rules, and optional per-image variation rules."""
    cleaned = user_prompt.strip()
    sections = [
        f"USER REQUEST:\n{cleaned}",
        STUDIO_COMPOSITION_RULES,
        FASHION_QUALITY_RULES,
    ]

    if total_images > 1 and image_index is not None:
        variation = format_multi_image_variation(
            image_index=image_index,
            total_images=total_images,
        )
        if variation:
            sections.append(variation)

    return "\n\n".join(sections)
