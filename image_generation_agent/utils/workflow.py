"""Automatic workflow selection from reference image count."""

from __future__ import annotations

from image_generation_agent.models.requests import Workflow


def detect_workflow(reference_count: int) -> Workflow:
    if reference_count == 0:
        return Workflow.TEXT_TO_IMAGE
    if reference_count == 1:
        return Workflow.IMAGE_TO_IMAGE
    return Workflow.MULTI_IMAGE_GENERATION
