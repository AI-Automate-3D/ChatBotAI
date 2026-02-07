"""Context retrieval — embed a question and query the Pinecone vector store.

Usage
-----
    from ChatBotGeneric.context import retrieve_context

    context = retrieve_context(
        question="How do I return an item?",
        openai_api_key="sk-...",
        pinecone_api_key="pk-...",
        index_name="my-index",
        namespace="chatbot",
    )
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import openai

from tools.pinecone.config import PineconeConfig
from tools.pinecone.vector_store import VectorStore

logger = logging.getLogger(__name__)


def make_embed_fn(api_key: str, model: str = "text-embedding-3-small"):
    """Create an OpenAI embedding function.

    Parameters
    ----------
    api_key : str
        OpenAI API key.
    model : str
        Embedding model name.

    Returns
    -------
    callable
        A function ``embed(text: str) -> list[float]``.
    """
    client = openai.OpenAI(api_key=api_key)

    def embed(text: str) -> list[float]:
        response = client.embeddings.create(input=text, model=model)
        return response.data[0].embedding

    return embed


def retrieve_context(
    question: str,
    openai_api_key: str,
    pinecone_api_key: str,
    index_name: str,
    namespace: str = "",
    embedding_model: str = "text-embedding-3-small",
    top_k: int = 5,
) -> str:
    """Retrieve relevant context from the Pinecone vector store.

    Parameters
    ----------
    question : str
        The user's question to find context for.
    openai_api_key : str
        OpenAI API key for generating embeddings.
    pinecone_api_key : str
        Pinecone API key.
    index_name : str
        Pinecone index name.
    namespace : str
        Pinecone namespace.
    embedding_model : str
        OpenAI embedding model name.
    top_k : int
        Number of context chunks to retrieve.

    Returns
    -------
    str
        Formatted context string (e.g. ``"[1] chunk1\\n\\n[2] chunk2"``).
        Returns an empty string if no relevant context is found.
    """
    pinecone_config = PineconeConfig(
        api_key=pinecone_api_key,
        index_name=index_name,
        namespace=namespace,
    )

    embed_fn = make_embed_fn(openai_api_key, embedding_model)
    store = VectorStore(pinecone_config, embed_fn=embed_fn)

    context = store.get_context(question, top_k=top_k)

    if context:
        chunk_count = context.count("[")
        logger.info("Retrieved %d context chunk(s) for: %s", chunk_count, question[:80])
    else:
        logger.warning("No relevant context found for: %s", question[:80])

    return context
