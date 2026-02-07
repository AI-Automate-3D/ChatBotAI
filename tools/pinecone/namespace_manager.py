"""Namespace management — list, delete, and copy namespaces.

Usage
-----
    from tools.pinecone.namespace_manager import (
        list_namespaces, delete_namespace, get_namespace_stats,
    )

    namespaces = list_namespaces(config)
    stats = get_namespace_stats(config, "chatbot")
    delete_namespace(config, "old-data", skip_confirm=True)
"""

from __future__ import annotations

import logging

from tools.pinecone.config import PineconeConfig
from tools.pinecone.client import get_index

logger = logging.getLogger(__name__)


def list_namespaces(config: PineconeConfig) -> dict[str, int]:
    """List all namespaces and their vector counts.

    Parameters
    ----------
    config : PineconeConfig
        Pinecone connection settings.

    Returns
    -------
    dict[str, int]
        Mapping of namespace name to vector count.
    """
    index = get_index(config)
    stats = index.describe_index_stats()
    namespaces = {}
    for ns, ns_stats in stats.get("namespaces", {}).items():
        namespaces[ns] = ns_stats.get("vector_count", 0)
    return namespaces


def get_namespace_stats(
    config: PineconeConfig,
    namespace: str | None = None,
) -> dict:
    """Get detailed stats for a specific namespace.

    Parameters
    ----------
    config : PineconeConfig
        Pinecone connection settings.
    namespace : str | None
        Namespace to inspect (defaults to config.namespace).

    Returns
    -------
    dict
        ``{"namespace", "vector_count", "exists"}``
    """
    ns = namespace or config.namespace
    all_ns = list_namespaces(config)

    if ns in all_ns:
        return {
            "namespace": ns,
            "vector_count": all_ns[ns],
            "exists": True,
        }
    return {
        "namespace": ns,
        "vector_count": 0,
        "exists": False,
    }


def delete_namespace(
    config: PineconeConfig,
    namespace: str | None = None,
    skip_confirm: bool = False,
) -> None:
    """Delete all vectors in a namespace.

    Parameters
    ----------
    config : PineconeConfig
        Pinecone connection settings.
    namespace : str | None
        Namespace to delete (defaults to config.namespace).
    skip_confirm : bool
        Skip interactive confirmation.
    """
    index = get_index(config)
    ns = namespace or config.namespace

    stats = get_namespace_stats(config, ns)
    if not stats["exists"]:
        logger.warning("Namespace '%s' does not exist or is empty.", ns)
        return

    logger.info(
        "Namespace '%s' contains %d vector(s).",
        ns, stats["vector_count"],
    )

    if not skip_confirm:
        answer = input(
            f"\nDelete ALL vectors in namespace '{ns}'? "
            f"This is irreversible. [y/N] "
        )
        if answer.strip().lower() not in ("y", "yes"):
            logger.info("Aborted.")
            return

    index.delete(delete_all=True, namespace=ns)
    logger.info("Deleted all vectors in namespace '%s'.", ns)


def copy_namespace(
    config: PineconeConfig,
    source_ns: str,
    target_ns: str,
    batch_size: int = 100,
) -> int:
    """Copy all vectors from one namespace to another.

    Uses list + fetch + upsert to move vectors between namespaces.
    Note: Pinecone's list endpoint requires ``list`` support on your
    index type (available on serverless indexes).

    Parameters
    ----------
    config : PineconeConfig
        Pinecone connection settings.
    source_ns : str
        Source namespace.
    target_ns : str
        Destination namespace.
    batch_size : int
        Number of vectors per batch.

    Returns
    -------
    int
        Number of vectors copied.
    """
    index = get_index(config)
    copied = 0
    pagination_token = None

    logger.info("Copying vectors from '%s' to '%s' ...", source_ns, target_ns)

    while True:
        # List vector IDs in source namespace
        list_kwargs = {"namespace": source_ns, "limit": batch_size}
        if pagination_token:
            list_kwargs["pagination_token"] = pagination_token

        list_response = index.list(**list_kwargs)
        vec_ids = [v for v in (list_response.get("vectors", []) or [])]

        if not vec_ids:
            break

        # Fetch full vectors
        fetch_response = index.fetch(ids=vec_ids, namespace=source_ns)
        vectors_data = fetch_response.get("vectors", {})

        # Upsert into target namespace
        batch = []
        for vec_id, vec_data in vectors_data.items():
            batch.append({
                "id": vec_id,
                "values": vec_data.get("values", []),
                "metadata": vec_data.get("metadata", {}),
            })

        if batch:
            index.upsert(vectors=batch, namespace=target_ns)
            copied += len(batch)
            logger.info("Copied %d vectors (%d total)", len(batch), copied)

        pagination_token = list_response.get("pagination", {}).get("next")
        if not pagination_token:
            break

    logger.info("Done. Copied %d vector(s) from '%s' to '%s'.", copied, source_ns, target_ns)
    return copied
