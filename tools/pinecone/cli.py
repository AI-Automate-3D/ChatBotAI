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
    python -m tools.pinecone.cli vectors delete --ids vec-1 vec-2
    python -m tools.pinecone.cli vectors delete-all --yes
    python -m tools.pinecone.cli vectors update-metadata --id vec-1 --metadata '{"text": "new"}'

JSON file format for upsert
----------------------------
Pre-computed vectors::

    [
        {"id": "doc-1", "values": [0.1, 0.2, ...], "metadata": {"text": "hello"}},
        ...
    ]

Text (requires --embed-provider, to be added later)::

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

from tools.pinecone.config import PineconeConfig
from tools.pinecone.index_manager import (
    create_index,
    delete_index,
    describe_index,
    list_indexes,
)
from tools.pinecone.vector_store import VectorStore


def _build_parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="pinecone-tools",
        description="Reusable Pinecone toolkit — index management & vector operations.",
    )
    root.add_argument(
        "--env-file",
        default=None,
        help="Path to a .env file (default: reads from environment)",
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

    p_upsert = vec_sub.add_parser("upsert", help="Upsert vectors from a JSON file")
    p_upsert.add_argument("--file", required=True,
                          help="JSON file with vector data")

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


def main() -> None:
    logging.basicConfig(
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        level=logging.INFO,
    )

    parser = _build_parser()
    args = parser.parse_args()

    cfg = PineconeConfig.from_env(env_file=args.env_file)
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
            with open(args.file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                sys.exit("ERROR: JSON file must contain a top-level array.")

            # Detect format: pre-computed vectors vs text
            if data and "values" in data[0]:
                store.upsert_vectors(data)
            else:
                sys.exit(
                    "ERROR: JSON items must have 'values' (pre-computed vectors). "
                    "Text-based upsert requires an embedding provider — coming soon."
                )

        elif args.action == "delete":
            store.delete_vectors(args.ids)

        elif args.action == "delete-all":
            store.delete_all(skip_confirm=args.yes)

        elif args.action == "update-metadata":
            metadata = json.loads(args.metadata)
            store.update_metadata(args.id, metadata)


if __name__ == "__main__":
    main()
