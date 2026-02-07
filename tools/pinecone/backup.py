"""Backup and restore — export/import vectors to/from JSON files.

Usage
-----
    from tools.pinecone.backup import export_namespace, import_vectors

    # Export all vectors in a namespace to a JSON file
    export_namespace(config, "chatbot", "backup.json")

    # Import vectors from a JSON file
    import_vectors(config, "backup.json", namespace="chatbot")

CLI
---
    python -m tools.pinecone.cli backup export --file backup.json
    python -m tools.pinecone.cli backup import --file backup.json
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from tools.pinecone.config import PineconeConfig
from tools.pinecone.client import get_index

logger = logging.getLogger(__name__)


def export_namespace(
    config: PineconeConfig,
    namespace: str | None = None,
    output_file: str | Path = "backup.json",
    batch_size: int = 100,
) -> int:
    """Export all vectors from a namespace to a JSON file.

    Parameters
    ----------
    config : PineconeConfig
        Pinecone connection settings.
    namespace : str | None
        Namespace to export (defaults to config.namespace).
    output_file : str | Path
        Output JSON file path.
    batch_size : int
        Number of vector IDs to fetch per batch.

    Returns
    -------
    int
        Number of vectors exported.
    """
    index = get_index(config)
    ns = namespace or config.namespace
    out = Path(output_file)

    all_vectors: list[dict] = []
    pagination_token = None

    logger.info("Exporting namespace '%s' ...", ns)

    while True:
        list_kwargs = {"namespace": ns, "limit": batch_size}
        if pagination_token:
            list_kwargs["pagination_token"] = pagination_token

        list_response = index.list(**list_kwargs)
        vec_ids = [v for v in (list_response.get("vectors", []) or [])]

        if not vec_ids:
            break

        fetch_response = index.fetch(ids=vec_ids, namespace=ns)
        vectors_data = fetch_response.get("vectors", {})

        for vec_id, vec_data in vectors_data.items():
            all_vectors.append({
                "id": vec_id,
                "values": vec_data.get("values", []),
                "metadata": vec_data.get("metadata", {}),
            })

        logger.info("Fetched %d vectors (%d total)", len(vectors_data), len(all_vectors))

        pagination_token = list_response.get("pagination", {}).get("next")
        if not pagination_token:
            break

    # Write to file
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(all_vectors, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    logger.info("Exported %d vector(s) to %s", len(all_vectors), out)
    return len(all_vectors)


def import_vectors(
    config: PineconeConfig,
    input_file: str | Path,
    namespace: str | None = None,
    batch_size: int = 100,
    replace: bool = False,
) -> int:
    """Import vectors from a JSON file into Pinecone.

    The JSON file should contain a list of dicts, each with
    ``id``, ``values``, and optionally ``metadata``.

    Parameters
    ----------
    config : PineconeConfig
        Pinecone connection settings.
    input_file : str | Path
        Path to the JSON file.
    namespace : str | None
        Target namespace (defaults to config.namespace).
    batch_size : int
        Number of vectors per upsert batch.
    replace : bool
        If *True*, delete all existing vectors in the namespace first.

    Returns
    -------
    int
        Number of vectors imported.
    """
    index = get_index(config)
    ns = namespace or config.namespace
    path = Path(input_file)

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON array, got {type(data).__name__}")

    if replace:
        logger.info("Replacing — deleting all vectors in namespace '%s'", ns)
        index.delete(delete_all=True, namespace=ns)

    imported = 0
    for i in range(0, len(data), batch_size):
        batch = data[i : i + batch_size]
        index.upsert(vectors=batch, namespace=ns)
        imported += len(batch)
        logger.info("Imported batch %d–%d of %d", i + 1, i + len(batch), len(data))

    logger.info("Imported %d vector(s) into namespace '%s'", imported, ns)
    return imported


def export_metadata_only(
    config: PineconeConfig,
    namespace: str | None = None,
    output_file: str | Path = "metadata_backup.json",
    batch_size: int = 100,
) -> int:
    """Export only metadata (no vectors) for a lighter backup.

    Useful for auditing or inspecting what's stored without downloading
    large embedding arrays.

    Parameters
    ----------
    config : PineconeConfig
        Pinecone connection settings.
    namespace : str | None
        Namespace to export.
    output_file : str | Path
        Output JSON file path.
    batch_size : int
        IDs per fetch batch.

    Returns
    -------
    int
        Number of entries exported.
    """
    index = get_index(config)
    ns = namespace or config.namespace
    out = Path(output_file)

    all_entries: list[dict] = []
    pagination_token = None

    while True:
        list_kwargs = {"namespace": ns, "limit": batch_size}
        if pagination_token:
            list_kwargs["pagination_token"] = pagination_token

        list_response = index.list(**list_kwargs)
        vec_ids = [v for v in (list_response.get("vectors", []) or [])]

        if not vec_ids:
            break

        fetch_response = index.fetch(ids=vec_ids, namespace=ns)
        vectors_data = fetch_response.get("vectors", {})

        for vec_id, vec_data in vectors_data.items():
            all_entries.append({
                "id": vec_id,
                "metadata": vec_data.get("metadata", {}),
            })

        pagination_token = list_response.get("pagination", {}).get("next")
        if not pagination_token:
            break

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(all_entries, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    logger.info("Exported metadata for %d vector(s) to %s", len(all_entries), out)
    return len(all_entries)
