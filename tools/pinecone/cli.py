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
    python -m tools.pinecone.cli vectors upsert --file data.txt
    python -m tools.pinecone.cli vectors upsert --file data.csv
    python -m tools.pinecone.cli vectors upsert --file knowledgebase.docx --replace
    python -m tools.pinecone.cli vectors fetch --ids vec-1 vec-2
    python -m tools.pinecone.cli vectors query --text "search terms" --top-k 5
    python -m tools.pinecone.cli vectors query --text "search" --filter '{"type": {"$eq": "faq"}}'
    python -m tools.pinecone.cli vectors delete --ids vec-1 vec-2
    python -m tools.pinecone.cli vectors delete-all --yes
    python -m tools.pinecone.cli vectors update-metadata --id vec-1 --metadata '{"text": "new"}'

    # Namespace operations
    python -m tools.pinecone.cli namespace list
    python -m tools.pinecone.cli namespace stats --ns chatbot
    python -m tools.pinecone.cli namespace delete --ns old-data --yes
    python -m tools.pinecone.cli namespace copy --from chatbot --to backup

    # Backup & restore
    python -m tools.pinecone.cli backup export --file backup.json
    python -m tools.pinecone.cli backup export --file metadata.json --metadata-only
    python -m tools.pinecone.cli backup import --file backup.json
    python -m tools.pinecone.cli backup import --file backup.json --replace

Supported file formats for upsert
-----------------------------------
.docx — Knowledge-base documents using ``--- KB_CHUNK_END ---`` separators.
.txt  — Plain text with delimiters or paragraph-based splitting.
.csv  — Tabular data with ``id``, ``text``, and optional metadata columns.
.json — Pre-computed vectors or text items (auto-detected).
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
from tools.pinecone.embeddings import make_embed_fn as _make_embed_fn

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_PROJECT_CONFIG = _PROJECT_ROOT / "_config files" / "config.json"


# ── argument parser ─────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="pinecone-tools",
        description="Reusable Pinecone toolkit — index, vector, namespace, and backup operations.",
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

    p_upsert = vec_sub.add_parser("upsert", help="Upsert vectors from a file")
    p_upsert.add_argument("--file", required=True,
                          help="File with vector/text data (.json, .docx, .txt, .csv)")
    p_upsert.add_argument("--embed-provider", default="openai",
                          choices=["openai"],
                          help="Embedding provider for text-based upsert (default: openai)")
    p_upsert.add_argument("--embed-model", default="text-embedding-3-small",
                          help="Embedding model name (default: text-embedding-3-small)")
    p_upsert.add_argument("--replace", action="store_true", default=False,
                          help="Delete all existing vectors in the namespace before upserting")

    p_fetch = vec_sub.add_parser("fetch", help="Fetch vectors by ID")
    p_fetch.add_argument("--ids", nargs="+", required=True,
                         help="Vector IDs to fetch")
    p_fetch.add_argument("--no-values", action="store_true", default=False,
                         help="Omit embedding values from output")

    p_query = vec_sub.add_parser("query", help="Semantic search with text")
    p_query.add_argument("--text", required=True,
                         help="Query text to embed and search")
    p_query.add_argument("--top-k", type=int, default=5,
                         help="Number of results (default: 5)")
    p_query.add_argument("--filter", default=None,
                         help="JSON metadata filter (e.g. '{\"type\": {\"$eq\": \"faq\"}}')")
    p_query.add_argument("--embed-provider", default="openai", choices=["openai"])
    p_query.add_argument("--embed-model", default="text-embedding-3-small")
    p_query.add_argument("--min-score", type=float, default=0.0,
                         help="Minimum similarity score to show (default: 0.0)")

    p_del = vec_sub.add_parser("delete", help="Delete vectors by ID")
    p_del.add_argument("--ids", nargs="+", required=True,
                       help="Vector IDs to delete")

    p_del_all = vec_sub.add_parser("delete-all", help="Delete all vectors in namespace")
    p_del_all.add_argument("--yes", "-y", action="store_true")

    p_meta = vec_sub.add_parser("update-metadata", help="Update metadata on a vector")
    p_meta.add_argument("--id", required=True, help="Vector ID")
    p_meta.add_argument("--metadata", required=True,
                        help="JSON string of metadata to set")

    # ── namespace sub-commands ─────────────────────────────────────────────
    ns_parser = sub.add_parser("namespace", help="Namespace operations")
    ns_sub = ns_parser.add_subparsers(dest="action", required=True)

    ns_sub.add_parser("list", help="List all namespaces with vector counts")

    p_ns_stats = ns_sub.add_parser("stats", help="Stats for a specific namespace")
    p_ns_stats.add_argument("--ns", default=None,
                            help="Namespace name (default: configured namespace)")

    p_ns_delete = ns_sub.add_parser("delete", help="Delete all vectors in a namespace")
    p_ns_delete.add_argument("--ns", default=None,
                             help="Namespace to delete")
    p_ns_delete.add_argument("--yes", "-y", action="store_true")

    p_ns_copy = ns_sub.add_parser("copy", help="Copy vectors between namespaces")
    p_ns_copy.add_argument("--from", dest="source_ns", required=True,
                           help="Source namespace")
    p_ns_copy.add_argument("--to", dest="target_ns", required=True,
                           help="Target namespace")

    # ── backup sub-commands ────────────────────────────────────────────────
    bk = sub.add_parser("backup", help="Backup & restore operations")
    bk_sub = bk.add_subparsers(dest="action", required=True)

    p_export = bk_sub.add_parser("export", help="Export vectors to a JSON file")
    p_export.add_argument("--file", required=True, help="Output JSON file path")
    p_export.add_argument("--metadata-only", action="store_true", default=False,
                          help="Export metadata only (no embedding values)")

    p_import = bk_sub.add_parser("import", help="Import vectors from a JSON file")
    p_import.add_argument("--file", required=True, help="Input JSON file path")
    p_import.add_argument("--replace", action="store_true", default=False,
                          help="Delete all existing vectors before importing")

    return root


# ── upsert handlers ────────────────────────────────────────────────────────

def _handle_upsert(store: VectorStore, args, json_config: dict | None = None) -> None:
    """Route upsert to the right handler based on file extension."""
    from tools.pinecone.parser import parse_file

    file_path = Path(args.file)
    ext = file_path.suffix.lower()

    # Optionally wipe the namespace first
    if args.replace:
        store.delete_all(skip_confirm=False)

    # Resolve OpenAI settings from JSON config (if available)
    openai_cfg = (json_config or {}).get("openai", {})
    openai_api_key = openai_cfg.get("api_key")
    embed_model = openai_cfg.get("embedding_model") or args.embed_model

    if ext == ".json":
        _upsert_json(store, args, embed_model, openai_api_key)
    elif ext in (".docx", ".txt", ".csv"):
        chunks = parse_file(str(file_path))
        if not chunks:
            sys.exit(f"ERROR: No valid chunks found in {file_path}")
        logger.info("Parsed %d chunk(s) from %s — embedding and upserting ...", len(chunks), file_path.name)
        embed_fn = _make_embed_fn(api_key=openai_api_key, model=embed_model)
        store.upsert_texts(chunks, embed_fn=embed_fn)
        logger.info("Done. Upserted %d chunk(s).", len(chunks))
    else:
        sys.exit(f"ERROR: Unsupported file format '{ext}'. Use .json, .docx, .txt, or .csv.")


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
        logger.info("Detected text-based JSON — embedding and upserting %d item(s) ...", len(data))
        embed_fn = _make_embed_fn(api_key=openai_api_key, model=embed_model)
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
        cfg = PineconeConfig.from_json(args.config)
        with open(args.config, "r", encoding="utf-8") as f:
            _json_config = json.load(f)
    elif args.env_file:
        cfg = PineconeConfig.from_env(env_file=args.env_file)
    elif _PROJECT_CONFIG.exists():
        cfg = PineconeConfig.from_json(str(_PROJECT_CONFIG))
        with open(_PROJECT_CONFIG, "r", encoding="utf-8") as f:
            _json_config = json.load(f)
    else:
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

        elif args.action == "fetch":
            results = store.fetch(args.ids)
            for vec in results:
                entry = {"id": vec["id"], "metadata": vec["metadata"]}
                if not args.no_values:
                    entry["values"] = vec["values"]
                print(json.dumps(entry, indent=2, default=str))

        elif args.action == "query":
            openai_cfg = _json_config.get("openai", {})
            api_key = openai_cfg.get("api_key")
            model = openai_cfg.get("embedding_model") or args.embed_model

            embed_fn = _make_embed_fn(api_key=api_key, model=model)
            store_with_embed = VectorStore(cfg, embed_fn=embed_fn)

            filter_dict = json.loads(args.filter) if args.filter else None
            results = store_with_embed.query_text(
                args.text, top_k=args.top_k, filter=filter_dict,
            )

            for match in results:
                if match["score"] < args.min_score:
                    continue
                text = match["metadata"].get("text", "")
                preview = text[:100] + "..." if len(text) > 100 else text
                print(f"  [{match['score']:.4f}] {match['id']}: {preview}")

            if not results:
                print("  (no matches)")

        elif args.action == "delete":
            store.delete_vectors(args.ids)

        elif args.action == "delete-all":
            store.delete_all(skip_confirm=args.yes)

        elif args.action == "update-metadata":
            metadata = json.loads(args.metadata)
            store.update_metadata(args.id, metadata)

    # ── namespace commands ──────────────────────────────────────────────────
    elif args.group == "namespace":
        from tools.pinecone.namespace_manager import (
            list_namespaces,
            get_namespace_stats,
            delete_namespace,
            copy_namespace,
        )

        if args.action == "list":
            namespaces = list_namespaces(cfg)
            if not namespaces:
                print("(no namespaces)")
            for ns, count in namespaces.items():
                print(f"  '{ns}': {count} vectors")

        elif args.action == "stats":
            stats = get_namespace_stats(cfg, namespace=args.ns)
            print(f"  namespace: {stats['namespace']}")
            print(f"  exists:    {stats['exists']}")
            print(f"  vectors:   {stats['vector_count']}")

        elif args.action == "delete":
            delete_namespace(cfg, namespace=args.ns, skip_confirm=args.yes)

        elif args.action == "copy":
            copied = copy_namespace(cfg, source_ns=args.source_ns, target_ns=args.target_ns)
            print(f"Copied {copied} vectors from '{args.source_ns}' to '{args.target_ns}'")

    # ── backup commands ────────────────────────────────────────────────────
    elif args.group == "backup":
        from tools.pinecone.backup import (
            export_namespace,
            export_metadata_only,
            import_vectors,
        )

        if args.action == "export":
            if args.metadata_only:
                count = export_metadata_only(cfg, output_file=args.file)
            else:
                count = export_namespace(cfg, output_file=args.file)
            print(f"Exported {count} vector(s) to {args.file}")

        elif args.action == "import":
            count = import_vectors(cfg, input_file=args.file, replace=args.replace)
            print(f"Imported {count} vector(s) from {args.file}")


if __name__ == "__main__":
    main()
