"""Parse knowledge-base files into chunks for Pinecone upsert.

Supports multiple formats:

- ``.docx`` — Structured KB format with ``--- KB_CHUNK_END ---`` delimiters
- ``.txt``  — Plain text with ``--- KB_CHUNK_END ---`` delimiters, or
               paragraph-based splitting
- ``.csv``  — Tabular data with ``id``, ``text``, and optional metadata columns

All parsers return a list of dicts ready for ``VectorStore.upsert_texts()``.

Usage
-----
    from tools.pinecone.parser import parse_file, parse_docx, parse_txt, parse_csv

    # Auto-detect format by extension
    chunks = parse_file("knowledgebase.docx")

    # Or call format-specific parsers
    chunks = parse_docx("knowledgebase.docx")
    chunks = parse_txt("data.txt")
    chunks = parse_csv("data.csv")
"""

from __future__ import annotations

import csv
import hashlib
import logging
import re
from pathlib import Path

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


# ── .txt parser ───────────────────────────────────────────────────────────────

def parse_txt(
    file_path: str | Path,
    paragraph_mode: bool = False,
    min_length: int = 20,
) -> list[dict]:
    """Parse a ``.txt`` file into upsert-ready chunks.

    If the file contains ``--- KB_CHUNK_END ---`` delimiters, it is parsed
    using the same structured format as ``.docx`` files.

    Otherwise (or if *paragraph_mode* is ``True``), the file is split on
    blank lines and each non-trivial paragraph becomes a chunk.

    Parameters
    ----------
    file_path : str | Path
        Path to the ``.txt`` file.
    paragraph_mode : bool
        Force paragraph-based splitting even if delimiters are found.
    min_length : int
        Minimum character length for a paragraph to be kept.

    Returns
    -------
    list[dict]
        Upsert-ready chunks with ``id`` and ``text``.
    """
    path = Path(file_path)
    raw_text = path.read_text(encoding="utf-8")

    # Try structured format first
    if not paragraph_mode and CHUNK_DELIMITER in raw_text:
        return parse_kb_text(raw_text)

    # Paragraph-based splitting
    paragraphs = re.split(r"\n\s*\n", raw_text)
    chunks: list[dict] = []

    for para in paragraphs:
        text = para.strip()
        if len(text) < min_length:
            continue

        chunk_id = _text_hash(text)
        chunks.append({
            "id": chunk_id,
            "text": text,
        })

    logger.info("Parsed %d paragraph(s) from %s", len(chunks), path.name)
    return chunks


# ── .csv parser ───────────────────────────────────────────────────────────────

def parse_csv(
    file_path: str | Path,
    id_column: str = "id",
    text_column: str = "text",
) -> list[dict]:
    """Parse a ``.csv`` file into upsert-ready chunks.

    The CSV must have at minimum a ``text`` column.  If an ``id`` column
    exists it is used as the vector ID; otherwise a hash-based ID is
    generated.  All other columns become metadata.

    Parameters
    ----------
    file_path : str | Path
        Path to the ``.csv`` file.
    id_column : str
        Column name for vector IDs (default ``"id"``).
    text_column : str
        Column name for the text content (default ``"text"``).

    Returns
    -------
    list[dict]
        Upsert-ready chunks.
    """
    path = Path(file_path)
    chunks: list[dict] = []

    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)

        if text_column not in (reader.fieldnames or []):
            raise ValueError(
                f"CSV file must have a '{text_column}' column. "
                f"Found: {reader.fieldnames}"
            )

        for row in reader:
            text = (row.get(text_column) or "").strip()
            if not text:
                continue

            chunk_id = (row.get(id_column) or "").strip() or _text_hash(text)

            entry: dict = {"id": chunk_id, "text": text}
            # Add remaining columns as metadata
            for key, value in row.items():
                if key not in (id_column, text_column) and value:
                    entry[key] = value.strip()

            chunks.append(entry)

    logger.info("Parsed %d row(s) from %s", len(chunks), path.name)
    return chunks


# ── auto-detect parser ────────────────────────────────────────────────────────

def parse_file(file_path: str | Path) -> list[dict]:
    """Auto-detect file format and parse into upsert-ready chunks.

    Supported extensions: ``.docx``, ``.txt``, ``.csv``.

    Parameters
    ----------
    file_path : str | Path
        Path to the knowledge-base file.

    Returns
    -------
    list[dict]
        Upsert-ready chunks.

    Raises
    ------
    ValueError
        If the file extension is not supported.
    """
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == ".docx":
        return parse_docx(str(path))
    elif ext == ".txt":
        return parse_txt(path)
    elif ext == ".csv":
        return parse_csv(path)
    else:
        raise ValueError(
            f"Unsupported file format '{ext}'. Use .docx, .txt, or .csv."
        )


def _text_hash(text: str) -> str:
    """Generate a short deterministic ID from text content."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
