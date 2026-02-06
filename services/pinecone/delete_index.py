"""Delete a Pinecone vector store (index).

Standalone script — run directly to delete an existing index:

    python -m services.pinecone.delete_index
    python -m services.pinecone.delete_index --name my-index
    python -m services.pinecone.delete_index --name my-index --yes
"""

import argparse
import logging
import sys

from pinecone import Pinecone

import config

logging.basicConfig(
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def delete_index(name: str | None = None, skip_confirm: bool = False) -> None:
    """Delete a Pinecone index.

    Args:
        name:         Index name. Defaults to PINECONE_INDEX_NAME from config.
        skip_confirm: If True, skip the interactive confirmation prompt.
    """
    index_name = name or config.PINECONE_INDEX_NAME

    pc = Pinecone(api_key=config.PINECONE_API_KEY)

    # Verify the index exists
    existing = [idx.name for idx in pc.list_indexes()]
    if index_name not in existing:
        logger.error("Index '%s' does not exist.", index_name)
        logger.info("Available indexes: %s", existing if existing else "(none)")
        return

    # Show details before deleting
    desc = pc.describe_index(index_name)
    logger.info("Found index '%s':", index_name)
    logger.info("  host:      %s", desc.host)
    logger.info("  dimension: %s", desc.dimension)
    logger.info("  metric:    %s", desc.metric)
    logger.info("  status:    %s", desc.status)

    # Confirm
    if not skip_confirm:
        answer = input(f"\nAre you sure you want to delete '{index_name}'? "
                       f"This action is irreversible. [y/N] ")
        if answer.strip().lower() not in ("y", "yes"):
            logger.info("Aborted.")
            return

    # Delete
    logger.info("Deleting index '%s' …", index_name)
    pc.delete_index(index_name)
    logger.info("Index '%s' has been deleted.", index_name)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Delete a Pinecone vector store index."
    )
    parser.add_argument(
        "--name",
        default=None,
        help="Index name (default: PINECONE_INDEX_NAME from .env)",
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        default=False,
        help="Skip confirmation prompt",
    )

    args = parser.parse_args()

    delete_index(name=args.name, skip_confirm=args.yes)


if __name__ == "__main__":
    main()
