"""Pinecone Index Updater — fetch a Google Doc and sync to Pinecone.

Takes a Google Docs link, fetches the KB document, parses it into chunks,
and upserts them into the Pinecone index. If the index is empty it populates
it; if it already has data it updates (upsert = insert or replace).

Usage:
    python -m pinecone_index_updater.updater "https://docs.google.com/document/d/1d5U.../edit?usp=drive_link"

    # Force full replacement (wipe index first)
    python -m pinecone_index_updater.updater "https://docs.google.com/document/d/1d5U.../edit" --replace
"""

import argparse
import logging
import re
import sys

from pinecone import Pinecone

import config
from services.google.docs import GoogleDocsClient
from services.openai.embeddings import OpenAIEmbeddings
from pinecone_index_updater.parser import parse_kb_document

logging.basicConfig(
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def extract_doc_id(url: str) -> str:
    """Extract the Google Docs document ID from a URL.

    Supports formats like:
        https://docs.google.com/document/d/DOC_ID/edit?usp=drive_link
        https://docs.google.com/document/d/DOC_ID/edit
        https://docs.google.com/document/d/DOC_ID
    """
    match = re.search(r"/document/d/([a-zA-Z0-9_-]+)", url)
    if not match:
        sys.exit(f"ERROR: Could not extract document ID from URL: {url}")
    return match.group(1)


def update_index_from_doc(
    doc_url: str,
    replace: bool = False,
    namespace: str | None = None,
) -> int:
    """Fetch a Google Doc KB and upsert its chunks into Pinecone.

    Args:
        doc_url:   Full Google Docs URL.
        replace:   If True, wipe the namespace before upserting.
        namespace: Pinecone namespace override.

    Returns:
        Number of chunks upserted.
    """
    ns = namespace or config.PINECONE_NAMESPACE

    # 1 — Extract document ID from URL
    doc_id = extract_doc_id(doc_url)
    logger.info("Document ID: %s", doc_id)

    # 2 — Fetch document text from Google Docs
    logger.info("Fetching document from Google Docs …")
    docs_client = GoogleDocsClient()
    raw_text = docs_client.get_document_text(doc_id)

    if not raw_text.strip():
        logger.error("Document is empty — nothing to do.")
        return 0

    # 3 — Parse KB chunks
    chunks = parse_kb_document(raw_text)
    if not chunks:
        logger.error("No valid KB chunks found in document.")
        return 0

    logger.info("Found %d KB chunks to process.", len(chunks))

    # 4 — Connect to Pinecone
    pc = Pinecone(api_key=config.PINECONE_API_KEY)
    index = pc.Index(config.PINECONE_INDEX_NAME)
    embeddings = OpenAIEmbeddings()

    # Check current index state
    stats = index.describe_index_stats()
    ns_stats = stats.get("namespaces", {}).get(ns, {})
    current_count = ns_stats.get("vector_count", 0)

    if current_count == 0:
        logger.info("Index namespace '%s' is empty — populating.", ns)
    elif replace:
        logger.info(
            "Index namespace '%s' has %d vectors — replacing (wipe + upsert).",
            ns, current_count,
        )
        index.delete(delete_all=True, namespace=ns)
        logger.info("Namespace cleared.")
    else:
        logger.info(
            "Index namespace '%s' has %d vectors — upserting (add/update).",
            ns, current_count,
        )

    # 5 — Embed and upsert in batches
    batch_size = 100
    total_upserted = 0

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        vectors = []
        for chunk in batch:
            # Combine title + text for a richer embedding
            embed_input = f"{chunk['title']}\n{chunk['text']}"
            embedding = embeddings.embed(embed_input)
            vectors.append({
                "id": chunk["id"],
                "values": embedding,
                "metadata": {
                    "text": chunk["text"],
                    "title": chunk["title"],
                    "type": chunk["type"],
                },
            })
        index.upsert(vectors=vectors, namespace=ns)
        total_upserted += len(vectors)
        logger.info("  upserted %d/%d chunks", total_upserted, len(chunks))

    logger.info("Done. %d chunks synced to Pinecone namespace '%s'.", total_upserted, ns)
    return total_upserted


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch a Google Docs KB and sync it to Pinecone.",
    )
    parser.add_argument(
        "url",
        help="Google Docs URL (e.g. https://docs.google.com/document/d/.../edit)",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        default=False,
        help="Wipe the namespace before upserting (full replacement)",
    )
    parser.add_argument(
        "--namespace",
        default=None,
        help="Pinecone namespace (default: PINECONE_NAMESPACE from .env)",
    )

    args = parser.parse_args()
    update_index_from_doc(
        doc_url=args.url,
        replace=args.replace,
        namespace=args.namespace,
    )


if __name__ == "__main__":
    main()
