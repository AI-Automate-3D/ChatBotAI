"""OpenAI Chat Model service.

Mirrors the "OpenAI Chat Model1" node in the workflow diagram.
"""

import logging

from openai import OpenAI

import config

logger = logging.getLogger(__name__)


class OpenAIChatModel:
    """Wrapper around OpenAI chat completions."""

    def __init__(self) -> None:
        self._client = OpenAI(api_key=config.OPENAI_API_KEY)
        self._model = config.OPENAI_CHAT_MODEL

    def complete(self, messages: list[dict]) -> str:
        """Send *messages* to the chat model and return the reply text."""
        logger.info("Calling OpenAI model=%s", self._model)
        response = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
        )
        return response.choices[0].message.content or ""
