"""Prompt builder tests."""

from image_generation_agent.prompts.fashion_quality_rules import FASHION_QUALITY_RULES
from image_generation_agent.utils.prompt_builder import build_generation_prompt


def test_build_generation_prompt_includes_user_request():
    result = build_generation_prompt("Generate a luxury evening gown")
    assert "USER REQUEST:" in result
    assert "Generate a luxury evening gown" in result


def test_build_generation_prompt_includes_fashion_rules():
    result = build_generation_prompt("Red dress on model")
    assert FASHION_QUALITY_RULES.splitlines()[0] in result
    assert "BACKGROUND" in result
    assert "MODEL FACE VISIBILITY" in result
    assert "FULL OUTFIT VISIBILITY" in result
    assert "OUTFIT DETAILS" in result
    assert "ZERO lines" in result
