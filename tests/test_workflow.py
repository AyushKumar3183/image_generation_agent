"""Workflow detection tests."""

import pytest

from image_generation_agent.models.requests import Workflow
from image_generation_agent.utils.workflow import detect_workflow


@pytest.mark.parametrize(
    ("count", "expected"),
    [
        (0, Workflow.TEXT_TO_IMAGE),
        (1, Workflow.IMAGE_TO_IMAGE),
        (2, Workflow.MULTI_IMAGE_GENERATION),
        (5, Workflow.MULTI_IMAGE_GENERATION),
    ],
)
def test_detect_workflow(count: int, expected: Workflow):
    assert detect_workflow(count) == expected
