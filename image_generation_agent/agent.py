"""Single ADK agent — the only entry point in this project."""

from google.adk.agents import Agent

from image_generation_agent.prompts.image_generation_agent_prompt import PROMPT
from image_generation_agent.tools.generate_image_tool import generate_image_tool
from image_generation_agent.utils.env import load_env

load_env()

root_agent = Agent(
    name="image_generation_agent",
    model="gemini-2.5-flash",
    description="Generates images from text prompts via generate_image_tool.",
    instruction=PROMPT,
    tools=[generate_image_tool],
)
