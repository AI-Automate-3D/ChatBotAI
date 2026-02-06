"""Create a new Pinecone vector store (index).

Standalone script — run directly to provision a new index:

    python -m services.pinecone.create_index
    python -m services.pinecone.create_index --name my-index --dimension 1536 --metric cosine

The defaults match the OpenAI text-embedding-3-small model (1536 dimensions).
"""

import argparse
import logging
import sys
import time

from pinecone import Pinecone, ServerlessSpec

import config

logging.basicConfig(
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Mapping of common OpenAI embedding models to their dimensions
EMBEDDING_DIMENSIONS = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536,
}


def create_index(
    name: str | None = None,
    dimension: int | None = None,
    metric: str = "cosine",
    cloud: str = "aws",
    region: str = "us-east-1",
) -> None:
    """Create a new Pinecone serverless index.

    Args:
        name:      Index name. Defaults to PINECONE_INDEX_NAME from config.
        dimension: Vector dimension. Defaults to the dimension matching
                   OPENAI_EMBEDDING_MODEL from config.
        metric:    Distance metric — "cosine", "euclidean", or "dotproduct".
        cloud:     Cloud provider for serverless ("aws", "gcp", "azure").
        region:    Cloud region (e.g. "us-east-1").
    """
    index_name = name or config.PINECONE_INDEX_NAME
    dim = dimension or EMBEDDING_DIMENSIONS.get(config.OPENAI_EMBEDDING_MODEL, 1536)

    pc = Pinecone(api_key=config.PINECONE_API_KEY)

    # Check if it already exists
    existing = [idx.name for idx in pc.list_indexes()]
    if index_name in existing:
        logger.info("Index '%s' already exists — skipping creation.", index_name)
        desc = pc.describe_index(index_name)
        logger.info("  dimension=%s  metric=%s  status=%s",
                     desc.dimension, desc.metric, desc.status)
        return

    logger.info(
        "Creating Pinecone index '%s' (dimension=%d, metric=%s, cloud=%s/%s) …",
        index_name, dim, metric, cloud, region,
    )

    pc.create_index(
        name=index_name,
        dimension=dim,
        metric=metric,
        spec=ServerlessSpec(cloud=cloud, region=region),
    )

    # Wait until ready
    logger.info("Waiting for index to be ready …")
    while True:
        desc = pc.describe_index(index_name)
        if desc.status.get("ready"):
            break
        time.sleep(2)

    logger.info("Index '%s' is ready!", index_name)
    logger.info("  host: %s", desc.host)
    logger.info("  dimension: %s", desc.dimension)
    logger.info("  metric: %s", desc.metric)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a new Pinecone vector store index."
    )
    parser.add_argument(
        "--name",
        default=None,
        help="Index name (default: PINECONE_INDEX_NAME from .env)",
    )
    parser.add_argument(
        "--dimension",
        type=int,
        default=None,
        help="Vector dimension (default: auto-detected from embedding model)",
    )
    parser.add_argument(
        "--metric",
        default="cosine",
        choices=["cosine", "euclidean", "dotproduct"],
        help="Distance metric (default: cosine)",
    )
    parser.add_argument(
        "--cloud",
        default="aws",
        choices=["aws", "gcp", "azure"],
        help="Cloud provider (default: aws)",
    )
    parser.add_argument(
        "--region",
        default="us-east-1",
        help="Cloud region (default: us-east-1)",
    )

    args = parser.parse_args()

    create_index(
        name=args.name,
        dimension=args.dimension,
        metric=args.metric,
        cloud=args.cloud,
        region=args.region,
    )


if __name__ == "__main__":
    main()
