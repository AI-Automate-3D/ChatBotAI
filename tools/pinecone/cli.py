"""Unified CLI for Pinecone tools.

Usage
-----
    # Index management
    python -m tools.pinecone.cli index create --dimension 1536
    python -m tools.pinecone.cli index delete --yes
    python -m tools.pinecone.cli index list
    python -m tools.pinecone.cli index describe

    # Vector operations
    python -m tools.pinecone.cli vectors stats
    python -m tools.pinecone.cli vectors upsert --file data.json
    python -m tools.pinecone.cli vectors upsert --file knowledgebase.docx
    python -m tools.pinecone.cli vectors upsert --file knowledgebase.docx --replace
    python -m tools.pinecone.cli vectors delete --ids vec-1 vec-2
    python -m tools.pinecone.cli vectors delete-all --yes
    python -m tools.pinecone.cli vectors update-metadata --id vec-1 --metadata '{"text": "new"}'

Supported file formats for upsert
-----------------------------------
.docx — Knowledge-base documents using ``--- KB_CHUNK_END ---`` separators.
        Each chunk must have KB_ID, TYPE, TITLE, and TEXT fields.
        Requires an embedding provider (default: OpenAI).

.json — Pre-computed vectors::

    [
        {"id": "doc-1", "values": [0.1, 0.2, ...], "metadata": {"text": "hello"}},
        ...
    ]

.json — Text (auto-embedded)::

    [
        {"id": "doc-1", "text": "hello world"},
        ...
    ]
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from tools.pinecone.config import PineconeConfig
from tools.pinecone.index_manager import (
    create_index,
    delete_index,
    describe_index,
    list_indexes,
)
from tools.pinecone.vector_store import VectorStore

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_PROJECT_CONFIG = _PROJECT_ROOT / "_config files" / "config.json"


# ── embedding helpers ───────────────────────────────────────────────────────

def _make_embed_fn(provider: str, model: str, api_key: str | None = None):
    """Build an embedding function from CLI arguments.

    Args:
        provider: Embedding provider name (currently only ``"openai"``).
        model:    Model identifier for the provider.
        api_key:  Optional API key. Falls back to the environment variable.

    Returns:
        A callable ``(str) -> list[float]`` suitable for
        :py:meth:`VectorStore.upsert_texts`.
    """
    if provider == "openai":
        try:
            import openai
        except ImportError:
            sys.exit(
                "ERROR: The 'openai' package is required for text-based upsert. "
                "Install it with: pip install openai"
            )

        client = openai.OpenAI(api_key=api_key) if api_key else openai.OpenAI()

        def embed(text: str) -> list[float]:
            response = client.embeddings.create(input=text, model=model)
            return response.data[0].embedding

        return embed

    sys.exit(f"ERROR: Unsupported embedding provider: {provider}")


# ── argument parser ─────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="pinecone-tools",
        description="Reusable Pinecone toolkit — index management & vector operations.",
    )
    config_group = root.add_mutually_exclusive_group()
    config_group.add_argument(
        "--config",
        default=None,
        help="Path to a JSON config file (default: config.json if it exists)",
    )
    config_group.add_argument(
        "--env-file",
        default=None,
        help="Path to a .env file (fallback if no JSON config)",
    )
    root.add_argument(
        "--namespace",
        default=None,
        help="Override the PINECONE_NAMESPACE env var for this run",
    )

    sub = root.add_subparsers(dest="group", required=True)

    # ── index sub-commands ─────────────────────────────────────────────────
    idx = sub.add_parser("index", help="Manage Pinecone indexes")
    idx_sub = idx.add_subparsers(dest="action", required=True)

    p_create = idx_sub.add_parser("create", help="Create a new index")
    p_create.add_argument("--dimension", type=int, default=1536,
                          help="Vector dimension (default: 1536)")
    p_create.add_argument("--metric", default="cosine",
                          choices=["cosine", "euclidean", "dotproduct"])

    p_delete = idx_sub.add_parser("delete", help="Delete the index")
    p_delete.add_argument("--yes", "-y", action="store_true")

    idx_sub.add_parser("list", help="List all indexes")
    idx_sub.add_parser("describe", help="Describe the configured index")

    # ── vector sub-commands ────────────────────────────────────────────────
    vec = sub.add_parser("vectors", help="Vector operations")
    vec_sub = vec.add_subparsers(dest="action", required=True)

    vec_sub.add_parser("stats", help="Show index statistics")

    p_upsert = vec_sub.add_parser("upsert", help="Upsert vectors from a .json or .docx file")
    p_upsert.add_argument("--file", required=True,
                          help="JSON or .docx file with vector/text data")
    p_upsert.add_argument("--embed-provider", default="openai",
                          choices=["openai"],
                          help="Embedding provider for text-based upsert (default: openai)")
    p_upsert.add_argument("--embed-model", default="text-embedding-3-small",
                          help="Embedding model name (default: text-embedding-3-small)")
    p_upsert.add_argument("--replace", action="store_true", default=False,
                          help="Delete all existing vectors in the namespace before upserting")

    p_del = vec_sub.add_parser("delete", help="Delete vectors by ID")
    p_del.add_argument("--ids", nargs="+", required=True,
                       help="Vector IDs to delete")

    p_del_all = vec_sub.add_parser("delete-all", help="Delete all vectors in namespace")
    p_del_all.add_argument("--yes", "-y", action="store_true")

    p_meta = vec_sub.add_parser("update-metadata", help="Update metadata on a vector")
    p_meta.add_argument("--id", required=True, help="Vector ID")
    p_meta.add_argument("--metadata", required=True,
                        help="JSON string of metadata to set")

    return root


# ── upsert handlers ────────────────────────────────────────────────────────

def _handle_upsert(store: VectorStore, args, json_config: dict | None = None) -> None:
    """Route upsert to the right handler based on file extension."""
    file_path = Path(args.file)
    ext = file_path.suffix.lower()

    # Optionally wipe the namespace first
    if args.replace:
        store.delete_all(skip_confirm=False)

    # Resolve OpenAI settings from JSON config (if available)
    openai_cfg = (json_config or {}).get("openai", {})
    openai_api_key = openai_cfg.get("api_key")
    embed_model = openai_cfg.get("embedding_model") or args.embed_model

    if ext == ".docx":
        _upsert_docx(store, args, embed_model, openai_api_key)
    elif ext == ".json":
        _upsert_json(store, args, embed_model, openai_api_key)
    else:
        sys.exit(f"ERROR: Unsupported file format '{ext}'. Use .json or .docx.")


def _upsert_docx(
    store: VectorStore,
    args,
    embed_model: str,
    openai_api_key: str | None = None,
) -> None:
    """Parse a .docx knowledge-base file and upsert its chunks."""
    from tools.pinecone.parser import parse_docx

    chunks = parse_docx(args.file)
    if not chunks:
        sys.exit("ERROR: No valid KB chunks found in .docx file.")

    logger.info("Parsed %d chunk(s) from .docx — embedding and upserting …", len(chunks))
    embed_fn = _make_embed_fn(args.embed_provider, embed_model, api_key=openai_api_key)
    store.upsert_texts(chunks, embed_fn=embed_fn)
    logger.info("Done. Upserted %d chunk(s).", len(chunks))


def _upsert_json(
    store: VectorStore,
    args,
    embed_model: str,
    openai_api_key: str | None = None,
) -> None:
    """Upsert from a JSON file (pre-computed vectors or text)."""
    with open(args.file, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        sys.exit("ERROR: JSON file must contain a top-level array.")

    if not data:
        sys.exit("ERROR: JSON file is empty.")

    # Pre-computed vectors (items have "values" key)
    if "values" in data[0]:
        store.upsert_vectors(data)
    # Text-based (items have "text" key — embed automatically)
    elif "text" in data[0]:
        logger.info("Detected text-based JSON — embedding and upserting %d item(s) …", len(data))
        embed_fn = _make_embed_fn(args.embed_provider, embed_model, api_key=openai_api_key)
        store.upsert_texts(data, embed_fn=embed_fn)
        logger.info("Done. Upserted %d item(s).", len(data))
    else:
        sys.exit(
            "ERROR: JSON items must have either 'values' (pre-computed vectors) "
            "or 'text' (to be embedded)."
        )


# ── main ────────────────────────────────────────────────────────────────────

def main() -> None:
    logging.basicConfig(
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        level=logging.INFO,
    )

    parser = _build_parser()
    args = parser.parse_args()

    # ── load config ───────────────────────────────────────────────────────
    _json_config = {}  # raw JSON data for non-Pinecone keys (e.g. openai)

    if args.config:
        # Explicit --config path
        cfg = PineconeConfig.from_json(args.config)
        with open(args.config, "r", encoding="utf-8") as f:
            _json_config = json.load(f)
    elif args.env_file:
        # Explicit --env-file path
        cfg = PineconeConfig.from_env(env_file=args.env_file)
    elif _PROJECT_CONFIG.exists():
        # Auto-detect config.json in project root
        cfg = PineconeConfig.from_json(str(_PROJECT_CONFIG))
        with open(_PROJECT_CONFIG, "r", encoding="utf-8") as f:
            _json_config = json.load(f)
    else:
        # Fallback to environment variables
        cfg = PineconeConfig.from_env()

    if args.namespace:
        cfg.namespace = args.namespace

    # ── index commands ─────────────────────────────────────────────────────
    if args.group == "index":
        if args.action == "create":
            create_index(cfg, dimension=args.dimension, metric=args.metric)
        elif args.action == "delete":
            delete_index(cfg, skip_confirm=args.yes)
        elif args.action == "list":
            names = list_indexes(cfg)
            for n in names:
                print(n)
            if not names:
                print("(no indexes found)")
        elif args.action == "describe":
            info = describe_index(cfg)
            for k, v in info.items():
                print(f"  {k}: {v}")

    # ── vector commands ────────────────────────────────────────────────────
    elif args.group == "vectors":
        store = VectorStore(cfg)

        if args.action == "stats":
            s = store.stats()
            print(f"Index: {cfg.index_name}")
            print(f"  total vectors: {s.get('total_vector_count', 0)}")
            print(f"  dimension:     {s.get('dimension', '?')}")
            for ns, ns_stats in s.get("namespaces", {}).items():
                print(f"  namespace '{ns}': {ns_stats.get('vector_count', 0)} vectors")

        elif args.action == "upsert":
            _handle_upsert(store, args, _json_config)

        elif args.action == "delete":
            store.delete_vectors(args.ids)

        elif args.action == "delete-all":
            store.delete_all(skip_confirm=args.yes)

        elif args.action == "update-metadata":
            metadata = json.loads(args.metadata)
            store.update_metadata(args.id, metadata)


if __name__ == "__main__":
    main()
