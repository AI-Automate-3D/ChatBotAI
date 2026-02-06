"""Parse .docx knowledge-base files into chunks for Pinecone upsert.

The expected document format uses ``--- KB_CHUNK_END ---`` as a delimiter
between entries.  Each entry contains structured metadata headers::

    KB_ID: jadedrose_shipping_standard
    TYPE: support
    TITLE: Standard Delivery
    TEXT:
    Standard Delivery: £3.99
    1-5 working days …

    --- KB_CHUNK_END ---

Usage
-----
    from tools.pinecone.parser import parse_docx

    chunks = parse_docx("knowledgebase.docx")
    # [{"id": "jadedrose_shipping_standard", "text": "Standard Delivery: …",
    #   "type": "support", "title": "Standard Delivery"}, …]

The output is ready to pass directly to ``VectorStore.upsert_texts()``.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

CHUNK_DELIMITER = "--- KB_CHUNK_END ---"


# ── public API ──────────────────────────────────────────────────────────────

def parse_docx(file_path: str) -> list[dict]:
    """Parse a ``.docx`` knowledge-base file into upsert-ready chunks.

    Args:
        file_path: Path to a ``.docx`` file whose text uses the
                   ``KB_ID / TYPE / TITLE / TEXT / --- KB_CHUNK_END ---``
                   format.

    Returns:
        A list of dicts with keys ``id``, ``text``, ``type``, ``title`` —
        ready for :py:meth:`VectorStore.upsert_texts`.
    """
    from docx import Document  # lazy import — only needed for .docx files

    doc = Document(file_path)
    raw_text = "\n".join(p.text for p in doc.paragraphs)
    return parse_kb_text(raw_text)


def parse_kb_text(raw_text: str) -> list[dict]:
    """Parse raw KB-formatted text into upsert-ready chunks.

    This works on plain text from any source (Google Docs, ``.txt`` files,
    etc.) as long as the content follows the ``KB_CHUNK_END`` format.

    Args:
        raw_text: Full document text with chunks separated by
                  ``--- KB_CHUNK_END ---``.

    Returns:
        A list of dicts with keys ``id``, ``text``, ``type``, ``title``.
    """
    segments = raw_text.split(CHUNK_DELIMITER)
    chunks: list[dict] = []

    for segment in segments:
        parsed = _parse_single_chunk(segment)
        if parsed is not None:
            chunks.append(parsed)

    logger.info("Parsed %d chunk(s) from knowledge-base text.", len(chunks))
    return chunks


# ── internal helpers ────────────────────────────────────────────────────────

def _parse_single_chunk(raw: str) -> dict | None:
    """Extract KB_ID, TYPE, TITLE, and TEXT from a single chunk segment.

    Returns ``None`` if the segment does not contain a valid ``KB_ID``
    (e.g. section headers or blank space between chunks).
    """
    # KB_ID is required — skip segments without one
    m_id = re.search(r"KB_ID:\s*(.+)", raw)
    if not m_id:
        return None

    kb_id = m_id.group(1).strip()

    # TYPE and TITLE are optional
    m_type = re.search(r"TYPE:\s*(.+)", raw)
    kb_type = m_type.group(1).strip() if m_type else ""

    m_title = re.search(r"TITLE:\s*(.+)", raw)
    kb_title = m_title.group(1).strip() if m_title else ""

    # TEXT: everything after the "TEXT:" line
    m_text = re.search(r"TEXT:\s*\n(.*)", raw, re.DOTALL)
    kb_text = m_text.group(1).strip() if m_text else ""

    if not kb_text:
        logger.warning("Chunk '%s' has no TEXT content — skipping.", kb_id)
        return None

    return {
        "id": kb_id,
        "text": kb_text,
        "type": kb_type,
        "title": kb_title,
    }
