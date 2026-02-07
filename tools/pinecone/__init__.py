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

    # Query with metadata filtering
    results = store.query(vector=[...], top_k=5, filter={"type": {"$eq": "faq"}})

    # Or with an embedding function (any provider)
    from tools.pinecone.embeddings import make_embed_fn
    embed = make_embed_fn(model="text-embedding-3-small")
    store = VectorStore(cfg, embed_fn=embed)
    store.upsert_texts([{"id": "doc-1", "text": "hello world"}])
    results = store.query_text("search query", top_k=5)

CLI usage
---------
    python -m tools.pinecone.cli index create --dimension 1536
    python -m tools.pinecone.cli vectors stats
    python -m tools.pinecone.cli vectors query --text "search terms"
    python -m tools.pinecone.cli namespace list
    python -m tools.pinecone.cli backup export --file backup.json
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
from tools.pinecone.parser import parse_docx, parse_kb_text, parse_txt, parse_csv, parse_file
from tools.pinecone.vector_store import VectorStore
from tools.pinecone.embeddings import make_embed_fn, embed_text, embed_batch
from tools.pinecone.fetch import fetch_vectors, fetch_one, vector_exists
from tools.pinecone.namespace_manager import (
    list_namespaces,
    get_namespace_stats,
    delete_namespace,
    copy_namespace,
)
from tools.pinecone.backup import export_namespace, import_vectors, export_metadata_only

__all__ = [
    # Config & client
    "PineconeConfig",
    "get_client",
    "get_index",
    # Vector store
    "VectorStore",
    # Index management
    "create_index",
    "delete_index",
    "describe_index",
    "list_indexes",
    # Parsing
    "parse_docx",
    "parse_kb_text",
    "parse_txt",
    "parse_csv",
    "parse_file",
    # Embeddings
    "make_embed_fn",
    "embed_text",
    "embed_batch",
    # Fetch
    "fetch_vectors",
    "fetch_one",
    "vector_exists",
    # Namespace management
    "list_namespaces",
    "get_namespace_stats",
    "delete_namespace",
    "copy_namespace",
    # Backup
    "export_namespace",
    "import_vectors",
    "export_metadata_only",
]
