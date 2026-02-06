"""Pinecone vector store with OpenAI embeddings.

Mirrors the "Pinecone Vector Store - Get Text1" and "Embeddings OpenAI2"
nodes in the workflow diagram.
"""

import logging

from openai import OpenAI
from pinecone import Pinecone

import config

logger = logging.getLogger(__name__)


class VectorStore:
    """Wraps Pinecone index + OpenAI embeddings for RAG retrieval."""

    def __init__(self) -> None:
        self._openai = OpenAI(api_key=config.OPENAI_API_KEY)
        self._pc = Pinecone(api_key=config.PINECONE_API_KEY)
        self._index = self._pc.Index(config.PINECONE_INDEX_NAME)
        self._namespace = config.PINECONE_NAMESPACE
        self._embed_model = config.OPENAI_EMBEDDING_MODEL

    # -- Embeddings (OpenAI) ------------------------------------------------

    def _embed(self, text: str) -> list[float]:
        """Generate an embedding vector for *text*."""
        response = self._openai.embeddings.create(
            input=text,
            model=self._embed_model,
        )
        return response.data[0].embedding

    # -- Retrieval (Pinecone) -----------------------------------------------

    def query(self, text: str, top_k: int = 5) -> list[dict]:
        """Return the top-k most relevant chunks for *text*.

        Each result dict has keys: ``id``, ``score``, ``text``.
        """
        vector = self._embed(text)
        results = self._index.query(
            vector=vector,
            top_k=top_k,
            include_metadata=True,
            namespace=self._namespace,
        )
        docs = []
        for match in results.get("matches", []):
            docs.append({
                "id": match["id"],
                "score": match["score"],
                "text": match.get("metadata", {}).get("text", ""),
            })
        return docs

    def get_context(self, text: str, top_k: int = 5) -> str:
        """Return a formatted string of retrieved context for the agent."""
        docs = self.query(text, top_k=top_k)
        if not docs:
            return ""
        chunks = []
        for i, doc in enumerate(docs, 1):
            chunks.append(f"[{i}] {doc['text']}")
        return "\n\n".join(chunks)

    # -- Ingestion ----------------------------------------------------------

    def upsert_texts(self, texts: list[dict]) -> None:
        """Upsert documents into Pinecone.

        *texts* is a list of dicts with keys ``id`` and ``text``.
        """
        vectors = []
        for item in texts:
            embedding = self._embed(item["text"])
            vectors.append({
                "id": item["id"],
                "values": embedding,
                "metadata": {"text": item["text"]},
            })
        self._index.upsert(vectors=vectors, namespace=self._namespace)
        logger.info("Upserted %d vectors into Pinecone", len(vectors))
