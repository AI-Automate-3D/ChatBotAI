"""Parser for the Jaded Rose KB document format.

Parses a Google Doc that uses the following chunk format:

    KB_ID: some_unique_id
    TYPE: support
    TITLE: Some Title
    TEXT:
    The body text of this knowledge base entry ...

    --- KB_CHUNK_END ---

Each chunk is extracted into a dict with keys:
    id, type, title, text
"""

import re
import logging

logger = logging.getLogger(__name__)

# Delimiter that separates KB entries
CHUNK_DELIMITER = "--- KB_CHUNK_END ---"


def parse_kb_document(raw_text: str) -> list[dict]:
    """Parse raw KB document text into a list of chunk dicts.

    Returns:
        A list of dicts, each with keys: ``id``, ``type``, ``title``, ``text``.
    """
    raw_chunks = raw_text.split(CHUNK_DELIMITER)
    chunks: list[dict] = []

    for raw in raw_chunks:
        chunk = _parse_single_chunk(raw)
        if chunk:
            chunks.append(chunk)

    logger.info("Parsed %d KB chunks from document", len(chunks))
    return chunks


def _parse_single_chunk(raw: str) -> dict | None:
    """Extract KB_ID, TYPE, TITLE, and TEXT from a single raw chunk.

    Returns None if the chunk doesn't contain a valid KB_ID.
    """
    # Match KB_ID
    id_match = re.search(r"KB_ID:\s*(.+)", raw)
    if not id_match:
        return None

    kb_id = id_match.group(1).strip()

    # Match TYPE (optional)
    type_match = re.search(r"TYPE:\s*(.+)", raw)
    kb_type = type_match.group(1).strip() if type_match else ""

    # Match TITLE (optional)
    title_match = re.search(r"TITLE:\s*(.+)", raw)
    kb_title = title_match.group(1).strip() if title_match else ""

    # Extract TEXT — everything after "TEXT:\n"
    text_match = re.search(r"TEXT:\s*\n(.*)", raw, re.DOTALL)
    kb_text = text_match.group(1).strip() if text_match else ""

    if not kb_text:
        logger.warning("Chunk '%s' has no TEXT content — skipping.", kb_id)
        return None

    return {
        "id": kb_id,
        "type": kb_type,
        "title": kb_title,
        "text": kb_text,
    }
