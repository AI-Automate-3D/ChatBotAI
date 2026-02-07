"""Fetch vectors by ID from Pinecone.

Standalone function — retrieve stored vectors and their metadata
without performing a similarity search.

Usage
-----
    from tools.pinecone.fetch import fetch_vectors, fetch_one

    results = fetch_vectors(config, ids=["doc-1", "doc-2"])
    single  = fetch_one(config, id="doc-1")
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from tools.pinecone.config import PineconeConfig
from tools.pinecone.client import get_index

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


def fetch_vectors(
    config: PineconeConfig,
    ids: list[str],
    namespace: str | None = None,
) -> list[dict]:
    """Fetch vectors by their IDs.

    Parameters
    ----------
    config : PineconeConfig
        Pinecone connection settings.
    ids : list[str]
        Vector IDs to fetch.
    namespace : str | None
        Namespace to fetch from (defaults to config.namespace).

    Returns
    -------
    list[dict]
        List of ``{"id", "values", "metadata"}`` dicts for each found vector.
        Missing IDs are silently omitted.
    """
    index = get_index(config)
    ns = namespace or config.namespace

    response = index.fetch(ids=ids, namespace=ns)
    vectors = response.get("vectors", {})

    results = []
    for vec_id, vec_data in vectors.items():
        results.append({
            "id": vec_id,
            "values": vec_data.get("values", []),
            "metadata": vec_data.get("metadata", {}),
        })

    logger.info(
        "Fetched %d of %d requested vector(s) from namespace '%s'",
        len(results), len(ids), ns,
    )
    return results


def fetch_one(
    config: PineconeConfig,
    id: str,
    namespace: str | None = None,
) -> dict | None:
    """Fetch a single vector by ID.

    Parameters
    ----------
    config : PineconeConfig
        Pinecone connection settings.
    id : str
        Vector ID.
    namespace : str | None
        Namespace to fetch from.

    Returns
    -------
    dict | None
        ``{"id", "values", "metadata"}`` or ``None`` if not found.
    """
    results = fetch_vectors(config, ids=[id], namespace=namespace)
    return results[0] if results else None


def vector_exists(
    config: PineconeConfig,
    id: str,
    namespace: str | None = None,
) -> bool:
    """Check whether a vector ID exists in the index.

    Parameters
    ----------
    config : PineconeConfig
        Pinecone connection settings.
    id : str
        Vector ID to check.
    namespace : str | None
        Namespace to check in.

    Returns
    -------
    bool
        ``True`` if the vector exists, ``False`` otherwise.
    """
    return fetch_one(config, id=id, namespace=namespace) is not None
