"""Embed a .docx knowledge base and upload to Pinecone.

One-file runner — parses a .docx, embeds with OpenAI, upserts to Pinecone.

Usage
-----
    # Interactive — prompts for model and file
    python tools/openai/OpenAI_embeddings.py

    # With arguments — no prompts
    python tools/openai/OpenAI_embeddings.py --file kb.docx --model small

    # Replace existing vectors before upserting
    python tools/openai/OpenAI_embeddings.py --file kb.docx --model small --replace
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import openai

# ── project root on sys.path so 'tools.*' imports work ──────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent        # tools/openai/
TOOLS_DIR = SCRIPT_DIR.parent                        # tools/
PROJECT_ROOT = TOOLS_DIR.parent                      # project root
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.pinecone.config import PineconeConfig
from tools.pinecone.index_manager import create_index, describe_index, list_indexes
from tools.pinecone.parser import parse_docx
from tools.pinecone.vector_store import VectorStore

logging.basicConfig(
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ── model definitions ───────────────────────────────────────────────────────

MODELS = {
    "small": {
        "name": "text-embedding-3-small",
        "dimensions": 1536,
        "description": "Faster, cheaper, good quality",
    },
    "large": {
        "name": "text-embedding-3-large",
        "dimensions": 3072,
        "description": "Higher quality, costs more",
    },
}


# ── config loading ──────────────────────────────────────────────────────────

def load_config(config_path: str = None) -> tuple[PineconeConfig, dict]:
    """Load Pinecone config and raw JSON from config file.

    Returns:
        (PineconeConfig, full JSON dict)
    """
    if config_path is None:
        config_path = str(PROJECT_ROOT / "_config files" / "config.json")
    path = Path(config_path)
    if not path.exists():
        sys.exit(
            f"ERROR: Config file not found: {config_path}\n"
            "Copy config.example.json to config.json and fill in your API keys."
        )

    cfg = PineconeConfig.from_json(str(path))
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return cfg, raw


# ── interactive prompts ─────────────────────────────────────────────────────

def prompt_model() -> str:
    """Ask the user to choose an embedding model. Returns 'small' or 'large'."""
    print("\n╭─────────────────────────────────────────╮")
    print("│        OpenAI Embedding Models          │")
    print("├─────────────────────────────────────────┤")
    print("│  1. text-embedding-3-small  (1536 dim)  │")
    print("│     Faster, cheaper, good quality        │")
    print("│                                         │")
    print("│  2. text-embedding-3-large  (3072 dim)  │")
    print("│     Higher quality, costs more           │")
    print("╰─────────────────────────────────────────╯")

    while True:
        choice = input("\nSelect model [1/2] (default: 1): ").strip()
        if choice in ("", "1"):
            return "small"
        if choice == "2":
            return "large"
        print("Invalid choice. Enter 1 or 2.")


def prompt_file() -> str:
    """Ask the user for a .docx file path."""
    # Check for files in __test_data/
    test_dir = PROJECT_ROOT / "__test_data"
    test_files = sorted(test_dir.rglob("*.docx")) if test_dir.exists() else []

    if test_files:
        print(f"\nFound .docx file(s) in __test_data/:")
        for i, f in enumerate(test_files, 1):
            print(f"  {i}. {f}")
        print()

        choice = input(f"Enter file path or press Enter for [{test_files[0]}]: ").strip()
        if not choice:
            return str(test_files[0])
        return choice
    else:
        return input("\nEnter path to .docx file: ").strip()


# ── index dimension check ──────────────────────────────────────────────────

def ensure_index(cfg: PineconeConfig, dimension: int) -> None:
    """Make sure the Pinecone index exists with the right dimension.

    - If the index doesn't exist, create it.
    - If it exists but has the wrong dimension, warn and offer to recreate.
    """
    existing = list_indexes(cfg)

    if cfg.index_name not in existing:
        print(f"\nIndex '{cfg.index_name}' does not exist. Creating with dimension={dimension} ...")
        create_index(cfg, dimension=dimension, metric="cosine")
        return

    # Index exists — check dimension
    info = describe_index(cfg)
    current_dim = info.get("dimension")

    if current_dim == dimension:
        return  # all good

    print(f"\n⚠  Dimension mismatch!")
    print(f"   Index '{cfg.index_name}' has dimension {current_dim}")
    print(f"   Selected model requires dimension {dimension}")
    print()
    print("   Options:")
    print("   1. Delete and recreate the index (loses all existing vectors)")
    print("   2. Abort")

    while True:
        choice = input("\n   Choose [1/2]: ").strip()
        if choice == "1":
            from tools.pinecone.index_manager import delete_index
            delete_index(cfg, skip_confirm=True)
            print(f"\n   Recreating index with dimension={dimension} ...")
            create_index(cfg, dimension=dimension, metric="cosine")
            return
        if choice == "2":
            sys.exit("Aborted.")
        print("   Invalid choice. Enter 1 or 2.")


# ── embedding function ──────────────────────────────────────────────────────

def make_embed_fn(api_key: str, model_name: str):
    """Create an embedding function using the OpenAI API.

    Args:
        api_key:    OpenAI API key.
        model_name: Full model name (e.g. 'text-embedding-3-small').

    Returns:
        Callable (str) -> list[float]
    """
    client = openai.OpenAI(api_key=api_key)

    def embed(text: str) -> list[float]:
        response = client.embeddings.create(input=text, model=model_name)
        return response.data[0].embedding

    return embed


# ── main ────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Embed a .docx knowledge base and upload to Pinecone.",
    )
    parser.add_argument(
        "--file", "-f",
        default=None,
        help="Path to a .docx knowledge-base file",
    )
    parser.add_argument(
        "--model", "-m",
        default=None,
        choices=["small", "large"],
        help="Embedding model: 'small' (1536 dim) or 'large' (3072 dim)",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        default=False,
        help="Delete all existing vectors before upserting",
    )
    parser.add_argument(
        "--config",
        default="config.json",
        help="Path to config.json (default: config.json)",
    )
    args = parser.parse_args()

    # ── load config ────────────────────────────────────────────────────────
    cfg, raw_config = load_config(args.config)
    openai_cfg = raw_config.get("openai", {})
    openai_api_key = openai_cfg.get("api_key", "")

    if not openai_api_key:
        sys.exit("ERROR: Missing 'openai.api_key' in config.json")

    # ── choose model ───────────────────────────────────────────────────────
    if args.model:
        model_key = args.model
    else:
        # Check if config.json has a preferred model
        configured_model = openai_cfg.get("embedding_model", "")
        if configured_model == "text-embedding-3-large":
            model_key = "large"
        elif configured_model == "text-embedding-3-small":
            model_key = "small"
        else:
            model_key = prompt_model()

    model = MODELS[model_key]
    print(f"\n✓ Model: {model['name']} ({model['dimensions']} dimensions)")

    # ── choose file ────────────────────────────────────────────────────────
    if args.file:
        file_path = args.file
    else:
        file_path = prompt_file()

    if not file_path:
        sys.exit("ERROR: No file provided.")

    path = Path(file_path)
    if not path.exists():
        sys.exit(f"ERROR: File not found: {file_path}")
    if path.suffix.lower() != ".docx":
        sys.exit(f"ERROR: Expected a .docx file, got '{path.suffix}'")

    print(f"✓ File:  {file_path}")

    # ── parse .docx ────────────────────────────────────────────────────────
    chunks = parse_docx(file_path)
    if not chunks:
        sys.exit("ERROR: No valid KB chunks found in the .docx file.")

    print(f"✓ Parsed {len(chunks)} chunk(s)")

    # ── ensure index exists with correct dimension ─────────────────────────
    ensure_index(cfg, model["dimensions"])

    # ── optionally replace ─────────────────────────────────────────────────
    store = VectorStore(cfg)

    if args.replace:
        print("\nReplacing existing vectors ...")
        store.delete_all(skip_confirm=True)

    # ── embed and upsert ───────────────────────────────────────────────────
    embed_fn = make_embed_fn(openai_api_key, model["name"])

    print(f"\nEmbedding and upserting {len(chunks)} chunk(s) ...")
    store.upsert_texts(chunks, embed_fn=embed_fn)

    # ── summary ────────────────────────────────────────────────────────────
    stats = store.stats()
    total = stats.get("total_vector_count", 0)
    namespaces = stats.get("namespaces", {})

    print("\n╭─────────────────────────────────────────╮")
    print("│              ✓ Complete!                 │")
    print("├─────────────────────────────────────────┤")
    print(f"│  Index:     {cfg.index_name:<27}│")
    print(f"│  Model:     {model['name']:<27}│")
    print(f"│  Dimension: {model['dimensions']:<27}│")
    print(f"│  Chunks:    {len(chunks):<27}│")
    print(f"│  Total:     {total:<27}│")
    for ns, ns_stats in namespaces.items():
        count = ns_stats.get("vector_count", 0)
        print(f"│  ns '{ns}': {count:<25}│")
    print("╰─────────────────────────────────────────╯")


if __name__ == "__main__":
    main()
