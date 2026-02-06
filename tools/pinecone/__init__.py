"""Reusable Pinecone toolkit.

Copy this ``tools/pinecone`` folder into any new project.  Configure via
environment variables (or a .env file) and you're ready to go.

Quick start
-----------
    from tools.pinecone import PineconeConfig, VectorStore

    cfg   = PineconeConfig.from_env()
    store = VectorStore(cfg)

    # Upsert pre-computed vectors
    store.upsert_vectors([
        {"id": "doc-1", "values": [...], "metadata": {"text": "..."}},
    ])

    # Query
    results = store.query(vector=[...], top_k=5)

    # Or with an embedding function (any provider)
    store = VectorStore(cfg, embed_fn=my_embed_function)
    store.upsert_texts([{"id": "doc-1", "text": "hello world"}])
    results = store.query_text("search query", top_k=5)

CLI usage
---------
    python -m tools.pinecone.cli index create --dimension 1536
    python -m tools.pinecone.cli vectors stats
    python -m tools.pinecone.cli --help
"""

from tools.pinecone.config import PineconeConfig
from tools.pinecone.client import get_client, get_index
from tools.pinecone.index_manager import (
    create_index,
    delete_index,
    describe_index,
    list_indexes,
)
from tools.pinecone.vector_store import VectorStore

__all__ = [
    "PineconeConfig",
    "VectorStore",
    "get_client",
    "get_index",
    "create_index",
    "delete_index",
    "describe_index",
    "list_indexes",
]
