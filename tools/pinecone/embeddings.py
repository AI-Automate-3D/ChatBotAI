"""Standalone embedding functions — decouple embedding from any specific vector store.

Provides a unified interface for generating embeddings from different
providers (OpenAI, Cohere, or custom).  Each function returns a standard
``list[float]`` vector or a list of vectors for batch calls.

Usage
-----
    from tools.pinecone.embeddings import embed_text, embed_batch, make_embed_fn

    # Single text
    vector = embed_text("hello world", api_key="sk-...", model="text-embedding-3-small")

    # Batch (more efficient — fewer API calls)
    vectors = embed_batch(["hello", "world"], api_key="sk-...", model="text-embedding-3-small")

    # Create a reusable function
    embed = make_embed_fn(api_key="sk-...", model="text-embedding-3-small")
    vec = embed("hello world")
"""

from __future__ import annotations

import logging
import sys
from typing import Callable

logger = logging.getLogger(__name__)

EmbedFn = Callable[[str], list[float]]

# ── model catalogue ──────────────────────────────────────────────────────────

OPENAI_MODELS = {
    "small": {
        "name": "text-embedding-3-small",
        "dimensions": 1536,
    },
    "large": {
        "name": "text-embedding-3-large",
        "dimensions": 3072,
    },
}


def get_model_dimensions(model: str) -> int:
    """Return the output dimension for a known embedding model.

    Parameters
    ----------
    model : str
        Full model name (e.g. ``"text-embedding-3-small"``) or short alias
        (``"small"``, ``"large"``).

    Returns
    -------
    int
        Embedding dimension, or 0 if unknown.
    """
    if model in OPENAI_MODELS:
        return OPENAI_MODELS[model]["dimensions"]
    for info in OPENAI_MODELS.values():
        if info["name"] == model:
            return info["dimensions"]
    return 0


def resolve_model_name(model: str) -> str:
    """Resolve a short alias to the full model name.

    ``"small"`` → ``"text-embedding-3-small"``
    ``"large"`` → ``"text-embedding-3-large"``
    Anything else passes through unchanged.
    """
    if model in OPENAI_MODELS:
        return OPENAI_MODELS[model]["name"]
    return model


# ── single text ──────────────────────────────────────────────────────────────

def embed_text(
    text: str,
    api_key: str | None = None,
    model: str = "text-embedding-3-small",
    provider: str = "openai",
) -> list[float]:
    """Embed a single piece of text.

    Parameters
    ----------
    text : str
        The text to embed.
    api_key : str | None
        API key for the provider.  Falls back to the standard env var
        (``OPENAI_API_KEY`` for OpenAI).
    model : str
        Model name or alias (``"small"`` / ``"large"``).
    provider : str
        Embedding provider (currently ``"openai"``).

    Returns
    -------
    list[float]
        The embedding vector.
    """
    model = resolve_model_name(model)
    fn = make_embed_fn(api_key=api_key, model=model, provider=provider)
    return fn(text)


# ── batch ────────────────────────────────────────────────────────────────────

def embed_batch(
    texts: list[str],
    api_key: str | None = None,
    model: str = "text-embedding-3-small",
    provider: str = "openai",
    batch_size: int = 100,
) -> list[list[float]]:
    """Embed multiple texts in batches.

    More efficient than calling ``embed_text`` in a loop because it
    batches API calls.

    Parameters
    ----------
    texts : list[str]
        Texts to embed.
    api_key : str | None
        Provider API key.
    model : str
        Model name or alias.
    provider : str
        Embedding provider.
    batch_size : int
        Number of texts per API call (default 100).

    Returns
    -------
    list[list[float]]
        List of embedding vectors (same order as input).
    """
    model = resolve_model_name(model)

    if provider != "openai":
        sys.exit(f"ERROR: Unsupported embedding provider: {provider}")

    try:
        import openai
    except ImportError:
        sys.exit("ERROR: pip install openai")

    client = openai.OpenAI(api_key=api_key) if api_key else openai.OpenAI()

    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        response = client.embeddings.create(input=batch, model=model)
        # Sort by index to preserve order
        sorted_data = sorted(response.data, key=lambda x: x.index)
        all_embeddings.extend([d.embedding for d in sorted_data])
        logger.info("Embedded batch %d–%d of %d", i + 1, i + len(batch), len(texts))

    return all_embeddings


# ── factory ──────────────────────────────────────────────────────────────────

def make_embed_fn(
    api_key: str | None = None,
    model: str = "text-embedding-3-small",
    provider: str = "openai",
) -> EmbedFn:
    """Create a reusable embedding function.

    Parameters
    ----------
    api_key : str | None
        Provider API key.
    model : str
        Model name or alias.
    provider : str
        Embedding provider (currently ``"openai"``).

    Returns
    -------
    EmbedFn
        A callable ``(str) -> list[float]``.
    """
    model = resolve_model_name(model)

    if provider != "openai":
        sys.exit(f"ERROR: Unsupported embedding provider: {provider}")

    try:
        import openai
    except ImportError:
        sys.exit("ERROR: pip install openai")

    client = openai.OpenAI(api_key=api_key) if api_key else openai.OpenAI()

    def embed(text: str) -> list[float]:
        response = client.embeddings.create(input=text, model=model)
        return response.data[0].embedding

    return embed
