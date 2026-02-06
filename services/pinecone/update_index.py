"""Update a Pinecone vector store (index).

Standalone script — run directly to update vectors in an existing index:

    # Upsert vectors from a JSON file
    python -m services.pinecone.update_index --file data.json

    # Update metadata on an existing vector
    python -m services.pinecone.update_index --update-id vec-1 --metadata '{"text": "new text"}'

    # Delete specific vectors by ID
    python -m services.pinecone.update_index --delete-ids vec-1 vec-2 vec-3

    # Delete all vectors in a namespace
    python -m services.pinecone.update_index --delete-all --yes

    # Show index stats
    python -m services.pinecone.update_index --stats

JSON file format for --file:
    [
        {"id": "doc-1", "text": "First document content ..."},
        {"id": "doc-2", "text": "Second document content ..."}
    ]
"""

import argparse
import json
import logging
import sys

from pinecone import Pinecone

import config
from services.openai.embeddings import OpenAIEmbeddings

logging.basicConfig(
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def _get_index():
    """Return a (Pinecone client, Index) tuple."""
    pc = Pinecone(api_key=config.PINECONE_API_KEY)
    index = pc.Index(config.PINECONE_INDEX_NAME)
    return pc, index


def show_stats(namespace: str | None = None) -> None:
    """Print index statistics."""
    pc, index = _get_index()
    stats = index.describe_index_stats()
    logger.info("Index: %s", config.PINECONE_INDEX_NAME)
    logger.info("  total vectors: %s", stats.get("total_vector_count", 0))
    logger.info("  dimension:     %s", stats.get("dimension", "?"))
    for ns, ns_stats in stats.get("namespaces", {}).items():
        logger.info("  namespace '%s': %s vectors", ns, ns_stats.get("vector_count", 0))


def upsert_from_file(filepath: str, namespace: str | None = None) -> None:
    """Upsert vectors from a JSON file.

    The file should contain a JSON array of objects with ``id`` and ``text`` keys.
    Each text is embedded via OpenAI and upserted into Pinecone.
    """
    ns = namespace or config.PINECONE_NAMESPACE
    embeddings = OpenAIEmbeddings()
    _, index = _get_index()

    with open(filepath, "r", encoding="utf-8") as f:
        documents = json.load(f)

    if not isinstance(documents, list):
        logger.error("JSON file must contain a top-level array of objects.")
        return

    logger.info("Upserting %d documents from '%s' …", len(documents), filepath)

    # Process in batches of 100
    batch_size = 100
    for i in range(0, len(documents), batch_size):
        batch = documents[i : i + batch_size]
        vectors = []
        for item in batch:
            doc_id = item.get("id")
            text = item.get("text", "")
            if not doc_id:
                logger.warning("Skipping document without 'id': %s", item)
                continue
            embedding = embeddings.embed(text)
            vectors.append({
                "id": doc_id,
                "values": embedding,
                "metadata": {"text": text},
            })
        if vectors:
            index.upsert(vectors=vectors, namespace=ns)
            logger.info("  upserted batch %d–%d", i + 1, i + len(vectors))

    logger.info("Done. Upserted documents into namespace '%s'.", ns)


def update_metadata(vector_id: str, metadata: dict, namespace: str | None = None) -> None:
    """Update metadata on an existing vector without changing its values."""
    ns = namespace or config.PINECONE_NAMESPACE
    _, index = _get_index()

    index.update(id=vector_id, set_metadata=metadata, namespace=ns)
    logger.info("Updated metadata for vector '%s' in namespace '%s'.", vector_id, ns)


def delete_vectors(ids: list[str], namespace: str | None = None) -> None:
    """Delete specific vectors by their IDs."""
    ns = namespace or config.PINECONE_NAMESPACE
    _, index = _get_index()

    index.delete(ids=ids, namespace=ns)
    logger.info("Deleted %d vector(s) from namespace '%s'.", len(ids), ns)


def delete_all(namespace: str | None = None, skip_confirm: bool = False) -> None:
    """Delete all vectors in a namespace."""
    ns = namespace or config.PINECONE_NAMESPACE
    _, index = _get_index()

    if not skip_confirm:
        answer = input(f"\nDelete ALL vectors in namespace '{ns}' of index "
                       f"'{config.PINECONE_INDEX_NAME}'? This is irreversible. [y/N] ")
        if answer.strip().lower() not in ("y", "yes"):
            logger.info("Aborted.")
            return

    index.delete(delete_all=True, namespace=ns)
    logger.info("Deleted all vectors in namespace '%s'.", ns)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Update vectors in a Pinecone index."
    )
    parser.add_argument(
        "--namespace",
        default=None,
        help="Pinecone namespace (default: PINECONE_NAMESPACE from .env)",
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--stats",
        action="store_true",
        help="Show index statistics",
    )
    group.add_argument(
        "--file",
        type=str,
        help="Path to a JSON file of documents to upsert (keys: id, text)",
    )
    group.add_argument(
        "--update-id",
        type=str,
        help="Vector ID whose metadata to update (use with --metadata)",
    )
    group.add_argument(
        "--delete-ids",
        nargs="+",
        help="Vector IDs to delete",
    )
    group.add_argument(
        "--delete-all",
        action="store_true",
        help="Delete all vectors in the namespace",
    )

    parser.add_argument(
        "--metadata",
        type=str,
        default=None,
        help='JSON string of metadata to set (used with --update-id). '
             'Example: \'{"text": "updated content"}\'',
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        default=False,
        help="Skip confirmation prompts",
    )

    args = parser.parse_args()

    if args.stats:
        show_stats(namespace=args.namespace)
    elif args.file:
        upsert_from_file(args.file, namespace=args.namespace)
    elif args.update_id:
        if not args.metadata:
            parser.error("--update-id requires --metadata")
        metadata = json.loads(args.metadata)
        update_metadata(args.update_id, metadata, namespace=args.namespace)
    elif args.delete_ids:
        delete_vectors(args.delete_ids, namespace=args.namespace)
    elif args.delete_all:
        delete_all(namespace=args.namespace, skip_confirm=args.yes)


if __name__ == "__main__":
    main()
