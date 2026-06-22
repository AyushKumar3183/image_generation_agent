"""ADK root agent — entry point for adk run / adk web chat."""

from image_generation_agent.utils.env import load_env
from image_generation_agent.utils.logging_config import configure_logging

load_env()
configure_logging()

from google.adk.agents import Agent

from image_generation_agent.prompts.image_generation_agent_prompt import PROMPT
from image_generation_agent.tools.generate_image_tool import generate_image_tool

root_agent = Agent(
    name="image_generation_agent",
    model="gemini-2.5-flash",
    description="Generates images from text prompts via generate_image_tool.",
    instruction=PROMPT,
    tools=[generate_image_tool],
)
