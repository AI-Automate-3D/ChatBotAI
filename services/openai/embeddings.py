"""OpenAI Embeddings service.

Mirrors the "Embeddings OpenAI2" node in the workflow diagram.
"""

import logging

from openai import OpenAI

import config

logger = logging.getLogger(__name__)


class OpenAIEmbeddings:
    """Wrapper around OpenAI text embeddings."""

    def __init__(self) -> None:
        self._client = OpenAI(api_key=config.OPENAI_API_KEY)
        self._model = config.OPENAI_EMBEDDING_MODEL

    def embed(self, text: str) -> list[float]:
        """Return the embedding vector for *text*."""
        response = self._client.embeddings.create(
            input=text,
            model=self._model,
        )
        return response.data[0].embedding

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Return embedding vectors for a batch of texts."""
        response = self._client.embeddings.create(
            input=texts,
            model=self._model,
        )
        return [item.embedding for item in response.data]
