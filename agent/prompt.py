"""Standalone system prompt loader — load prompts from .txt, .docx, or inline.

Handles loading system prompts from various sources so other modules
don't need to worry about file formats.

Usage
-----
    from agent.prompt import load_prompt

    # From a .txt file
    prompt = load_prompt("agent/system_prompt.txt")

    # From a .docx file
    prompt = load_prompt("agent/system_prompt.docx")

    # Inline fallback
    prompt = load_prompt(None, default="You are a helpful assistant.")
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_DEFAULT_PROMPT = (
    "You are a helpful assistant. Answer questions using only the "
    "provided context. If you don't know the answer, say so honestly."
)


def load_prompt(
    prompt_path: str | Path | None = None,
    default: str | None = None,
) -> str:
    """Load a system prompt from a file or return a default.

    Parameters
    ----------
    prompt_path : str | Path | None
        Path to a ``.txt`` or ``.docx`` file.  If ``None`` or the file
        does not exist, the *default* is returned.
    default : str | None
        Fallback prompt text.  If ``None``, a built-in default is used.

    Returns
    -------
    str
        The system prompt text.

    Raises
    ------
    FileNotFoundError
        If *prompt_path* is given but the file does not exist and no
        *default* is provided.
    """
    fallback = default if default is not None else _DEFAULT_PROMPT

    if prompt_path is None:
        return fallback

    path = Path(prompt_path)

    if not path.exists():
        if default is not None:
            logger.warning("Prompt file not found: %s — using default", path)
            return fallback
        raise FileNotFoundError(f"System prompt file not found: {path}")

    if path.suffix.lower() == ".docx":
        return _load_docx(path)

    return _load_text(path)


def _load_text(path: Path) -> str:
    """Load a plain-text prompt file."""
    text = path.read_text(encoding="utf-8").strip()
    logger.info("Loaded system prompt from %s (%d chars)", path, len(text))
    return text


def _load_docx(path: Path) -> str:
    """Load a .docx prompt file (requires python-docx)."""
    from docx import Document as DocxDocument

    doc = DocxDocument(str(path))
    text = "\n".join(p.text for p in doc.paragraphs).strip()
    logger.info("Loaded system prompt from %s (%d chars)", path, len(text))
    return text
