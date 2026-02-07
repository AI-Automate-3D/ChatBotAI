"""System prompt loader — load the system message from a local text file.

Usage
-----
    from ChatBotGeneric.prompt import load_prompt

    prompt = load_prompt("system_message.txt")
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
    """Load a system prompt from a text file or return a default.

    Parameters
    ----------
    prompt_path : str | Path | None
        Path to a ``.txt`` file.  If ``None`` or the file does not
        exist, the *default* is returned.
    default : str | None
        Fallback prompt text.  If ``None``, a built-in default is used.

    Returns
    -------
    str
        The system prompt text.
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

    text = path.read_text(encoding="utf-8").strip()
    logger.info("Loaded system prompt from %s (%d chars)", path, len(text))
    return text
