"""Pinecone index management — create, delete, list, describe.

Standalone CLI usage
--------------------
    python -m tools.pinecone.index_manager create
    python -m tools.pinecone.index_manager create --dimension 3072 --metric dotproduct
    python -m tools.pinecone.index_manager delete
    python -m tools.pinecone.index_manager delete --yes
    python -m tools.pinecone.index_manager list
    python -m tools.pinecone.index_manager describe

All commands read PINECONE_API_KEY and PINECONE_INDEX_NAME from
environment variables (or a .env file).
"""

from __future__ import annotations

import argparse
import logging
import time

from pinecone import Pinecone, ServerlessSpec

from tools.pinecone.config import PineconeConfig
from tools.pinecone.client import get_client

logger = logging.getLogger(__name__)


# ── Create ─────────────────────────────────────────────────────────────────

def create_index(
    config: PineconeConfig,
    dimension: int = 1536,
    metric: str = "cosine",
) -> None:
    """Create a Pinecone serverless index.

    Args:
        config:    PineconeConfig with api_key, index_name, cloud, region.
        dimension: Vector dimension (must match your embedding model).
        metric:    Distance metric — "cosine", "euclidean", or "dotproduct".
    """
    pc = get_client(config)
    name = config.index_name

    existing = [idx.name for idx in pc.list_indexes()]
    if name in existing:
        logger.info("Index '%s' already exists — skipping creation.", name)
        desc = pc.describe_index(name)
        logger.info("  dimension=%s  metric=%s  status=%s",
                     desc.dimension, desc.metric, desc.status)
        return

    logger.info(
        "Creating index '%s' (dimension=%d, metric=%s, cloud=%s/%s) …",
        name, dimension, metric, config.cloud, config.region,
    )

    pc.create_index(
        name=name,
        dimension=dimension,
        metric=metric,
        spec=ServerlessSpec(cloud=config.cloud, region=config.region),
    )

    # Wait until ready
    logger.info("Waiting for index to be ready …")
    while True:
        desc = pc.describe_index(name)
        if desc.status.get("ready"):
            break
        time.sleep(2)

    logger.info("Index '%s' is ready!", name)
    logger.info("  host:      %s", desc.host)
    logger.info("  dimension: %s", desc.dimension)
    logger.info("  metric:    %s", desc.metric)


# ── Delete ─────────────────────────────────────────────────────────────────

def delete_index(
    config: PineconeConfig,
    skip_confirm: bool = False,
) -> None:
    """Delete a Pinecone index.

    Args:
        config:       PineconeConfig with api_key and index_name.
        skip_confirm: If True, skip the interactive confirmation prompt.
    """
    pc = get_client(config)
    name = config.index_name

    existing = [idx.name for idx in pc.list_indexes()]
    if name not in existing:
        logger.error("Index '%s' does not exist.", name)
        logger.info("Available indexes: %s", existing or "(none)")
        return

    desc = pc.describe_index(name)
    logger.info("Found index '%s':", name)
    logger.info("  host:      %s", desc.host)
    logger.info("  dimension: %s", desc.dimension)
    logger.info("  metric:    %s", desc.metric)
    logger.info("  status:    %s", desc.status)

    if not skip_confirm:
        answer = input(
            f"\nAre you sure you want to delete '{name}'? "
            f"This action is irreversible. [y/N] "
        )
        if answer.strip().lower() not in ("y", "yes"):
            logger.info("Aborted.")
            return

    logger.info("Deleting index '%s' …", name)
    pc.delete_index(name)
    logger.info("Index '%s' has been deleted.", name)


# ── List ───────────────────────────────────────────────────────────────────

def list_indexes(config: PineconeConfig) -> list[str]:
    """Return a list of all index names on this account."""
    pc = get_client(config)
    indexes = [idx.name for idx in pc.list_indexes()]
    return indexes


# ── Describe ───────────────────────────────────────────────────────────────

def describe_index(config: PineconeConfig) -> dict:
    """Return metadata about the configured index.

    Returns a dict with keys: name, host, dimension, metric, status.
    """
    pc = get_client(config)
    desc = pc.describe_index(config.index_name)
    return {
        "name": config.index_name,
        "host": desc.host,
        "dimension": desc.dimension,
        "metric": desc.metric,
        "status": desc.status,
    }


# ── CLI ────────────────────────────────────────────────────────────────────

def main() -> None:
    logging.basicConfig(
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        level=logging.INFO,
    )

    parser = argparse.ArgumentParser(
        description="Manage Pinecone indexes (create / delete / list / describe)."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # create
    p_create = sub.add_parser("create", help="Create a new index")
    p_create.add_argument("--dimension", type=int, default=1536,
                          help="Vector dimension (default: 1536)")
    p_create.add_argument("--metric", default="cosine",
                          choices=["cosine", "euclidean", "dotproduct"],
                          help="Distance metric (default: cosine)")

    # delete
    p_delete = sub.add_parser("delete", help="Delete the index")
    p_delete.add_argument("--yes", "-y", action="store_true",
                          help="Skip confirmation prompt")

    # list
    sub.add_parser("list", help="List all indexes on the account")

    # describe
    sub.add_parser("describe", help="Show details about the configured index")

    args = parser.parse_args()
    cfg = PineconeConfig.from_env()

    if args.command == "create":
        create_index(cfg, dimension=args.dimension, metric=args.metric)
    elif args.command == "delete":
        delete_index(cfg, skip_confirm=args.yes)
    elif args.command == "list":
        names = list_indexes(cfg)
        for n in names:
            print(n)
        if not names:
            print("(no indexes found)")
    elif args.command == "describe":
        info = describe_index(cfg)
        for k, v in info.items():
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
