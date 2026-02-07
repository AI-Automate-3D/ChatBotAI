"""Standalone context retrieval — embed a question and query the vector store.

Wraps the Pinecone vector store query to provide a simple interface for
RAG (Retrieval-Augmented Generation) context retrieval.  Can be used
independently in any project that has a Pinecone index and OpenAI
embeddings.

Usage
-----
    from agent.context import retrieve_context

    context = retrieve_context(
        question="How do I return an item?",
        openai_api_key="sk-...",
        embedding_model="text-embedding-3-small",
        config_path="config.json",
        top_k=5,
    )
    print(context)  # "[1] Returns policy text...\n\n[2] ..."
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


from typing import Callable

EmbedFn = Callable[[str], list[float]]


def make_embed_fn(api_key: str, model: str = "text-embedding-3-small") -> EmbedFn:
    """Create an OpenAI embedding function.

    Parameters
    ----------
    api_key : str
        OpenAI API key.
    model : str
        Embedding model name.

    Returns
    -------
    EmbedFn
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
    embedding_model: str = "text-embedding-3-small",
    config_path: str | Path | None = None,
    pinecone_config: PineconeConfig | None = None,
    top_k: int = 5,
    namespace: str | None = None,
) -> str:
    """Retrieve relevant context from the vector store for a question.

    Parameters
    ----------
    question : str
        The user's question to find context for.
    openai_api_key : str
        OpenAI API key for generating embeddings.
    embedding_model : str
        OpenAI embedding model name.
    config_path : str | Path | None
        Path to config.json.  Used to create a ``PineconeConfig`` if
        *pinecone_config* is not provided.  Defaults to the project
        root ``_config files/config.json``.
    pinecone_config : PineconeConfig | None
        Pre-built Pinecone config.  Takes priority over *config_path*.
    top_k : int
        Number of context chunks to retrieve.
    namespace : str | None
        Pinecone namespace override.

    Returns
    -------
    str
        Formatted context string (e.g. ``"[1] chunk1\\n\\n[2] chunk2"``).
        Returns an empty string if no relevant context is found.
    """
    # Build Pinecone config
    if pinecone_config is None:
        path = str(config_path) if config_path else str(
            PROJECT_ROOT / "_config files" / "config.json"
        )
        pinecone_config = PineconeConfig.from_json(path)

    if namespace:
        pinecone_config.namespace = namespace

    # Create embedding function and vector store
    embed_fn = make_embed_fn(openai_api_key, embedding_model)
    store = VectorStore(pinecone_config, embed_fn=embed_fn)

    # Query
    context = store.get_context(question, top_k=top_k)

    if context:
        chunk_count = context.count("[")
        logger.info("Retrieved %d context chunk(s) for: %s", chunk_count, question[:80])
    else:
        logger.warning("No relevant context found for: %s", question[:80])

    return context


def retrieve_raw_results(
    question: str,
    openai_api_key: str,
    embedding_model: str = "text-embedding-3-small",
    config_path: str | Path | None = None,
    pinecone_config: PineconeConfig | None = None,
    top_k: int = 5,
    namespace: str | None = None,
) -> list[dict]:
    """Retrieve raw vector search results (with scores and metadata).

    Same as ``retrieve_context`` but returns the raw match list instead
    of a formatted string.  Useful when you need scores for filtering
    or metadata for routing.

    Parameters
    ----------
    question : str
        The user's question.
    openai_api_key : str
        OpenAI API key.
    embedding_model : str
        OpenAI embedding model name.
    config_path : str | Path | None
        Path to config.json.
    pinecone_config : PineconeConfig | None
        Pre-built Pinecone config.
    top_k : int
        Number of results to retrieve.
    namespace : str | None
        Pinecone namespace override.

    Returns
    -------
    list[dict]
        List of ``{"id": str, "score": float, "metadata": dict}`` dicts.
    """
    if pinecone_config is None:
        path = str(config_path) if config_path else str(
            PROJECT_ROOT / "_config files" / "config.json"
        )
        pinecone_config = PineconeConfig.from_json(path)

    if namespace:
        pinecone_config.namespace = namespace

    embed_fn = make_embed_fn(openai_api_key, embedding_model)
    store = VectorStore(pinecone_config, embed_fn=embed_fn)

    return store.query_text(question, top_k=top_k)
