"""Run root_agent via ADK Runner — shared entry for API and adk web/chat."""

from __future__ import annotations

import json
import logging
import uuid
from contextlib import aclosing

from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.adk.events.event import Event
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types

from image_generation_agent.agent import root_agent
from image_generation_agent.tools.generate_image_tool import generate_image_tool

logger = logging.getLogger(__name__)

TOOL_NAME = generate_image_tool.__name__
APP_NAME = "image_generation_agent"


class ImageGenerationAgentRunner:
    """Invokes root_agent so every request follows Agent → Tool → Service."""

    def __init__(self) -> None:
        self._session_service = InMemorySessionService()
        self._artifact_service = InMemoryArtifactService()
        self._runner = Runner(
            app_name=APP_NAME,
            agent=root_agent,
            session_service=self._session_service,
            artifact_service=self._artifact_service,
            auto_create_session=True,
        )

    @staticmethod
    def build_user_message(
        *,
        prompt: str,
        reference_images: list[str],
        resolution: str,
        number_of_images: int,
    ) -> str:
        """Structured message the agent maps to generate_image_tool args."""
        return json.dumps(
            {
                "prompt": prompt,
                "reference_images": reference_images,
                "resolution": resolution,
                "number_of_images": number_of_images,
            }
        )

    async def generate(
        self,
        *,
        prompt: str,
        reference_images: list[str] | None = None,
        resolution: str = "1K",
        number_of_images: int = 1,
    ) -> dict:
        refs = reference_images or []
        session_id = str(uuid.uuid4())
        user_message = self.build_user_message(
            prompt=prompt,
            reference_images=refs,
            resolution=resolution,
            number_of_images=number_of_images,
        )

        events: list[Event] = []
        async with aclosing(
            self._runner.run_async(
                user_id="api",
                session_id=session_id,
                new_message=types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=user_message)],
                ),
            )
        ) as event_stream:
            async for event in event_stream:
                events.append(event)

        payload = self._extract_tool_payload(events)
        if payload is not None:
            return payload

        logger.error("Agent did not return tool response session_id=%s", session_id)
        return {
            "status": "error",
            "error_code": "AGENT_NO_TOOL_RESPONSE",
            "message": "Agent did not return a generate_image_tool result.",
            "retryable": True,
            "request_id": session_id,
        }

    @classmethod
    def _extract_tool_payload(cls, events: list[Event]) -> dict | None:
        for event in reversed(events):
            for response in event.get_function_responses():
                if response.name != TOOL_NAME:
                    continue
                payload = cls._normalize_payload(response.response)
                if payload is not None:
                    return payload

        for event in reversed(events):
            if not event.is_final_response() or not event.content or not event.content.parts:
                continue
            for part in event.content.parts:
                if not part.text:
                    continue
                payload = cls._normalize_payload(part.text)
                if payload is not None:
                    return payload
        return None

    @staticmethod
    def _normalize_payload(value: object) -> dict | None:
        if isinstance(value, dict):
            return value if value.get("status") else None
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                return None
            return parsed if isinstance(parsed, dict) and parsed.get("status") else None
        return None
