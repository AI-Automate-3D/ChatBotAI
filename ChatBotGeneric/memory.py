"""Conversation memory manager — load, save, clear, and trim history.

Manages conversation history as a JSON file containing a list of
OpenAI-style message dicts (``{"role": "user"|"assistant", "content": "..."}``).

The number of past exchanges kept in context is controlled by
``max_history`` in config.json under the ``agent`` key.

Usage
-----
    from ChatBotGeneric.memory import load_memory, save_memory, append_exchange

    history = load_memory("memory.json")
    history = append_exchange(history, "Hello", "Hi there!")
    save_memory("memory.json", history, max_pairs=10)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def load_memory(memory_path: str | Path) -> list[dict]:
    """Load conversation history from a JSON file.

    Parameters
    ----------
    memory_path : str | Path
        Path to the memory JSON file.

    Returns
    -------
    list[dict]
        List of message dicts.  Returns an empty list if the file
        does not exist or is invalid.
    """
    path = Path(memory_path)
    if not path.exists():
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to load memory from %s: %s", path, exc)
        return []


def save_memory(
    memory_path: str | Path,
    history: list[dict],
    max_pairs: int = 10,
) -> None:
    """Save conversation history, trimmed to the last *max_pairs* exchanges.

    Each "pair" is one user message + one assistant message (2 entries).

    Parameters
    ----------
    memory_path : str | Path
        Path to the memory JSON file.
    history : list[dict]
        Full list of message dicts.
    max_pairs : int
        Maximum number of user/assistant pairs to keep.
        Set to 0 to keep nothing, or a negative value to keep all.
    """
    path = Path(memory_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if max_pairs >= 0:
        max_messages = max_pairs * 2
        trimmed = history[-max_messages:] if max_messages > 0 else []
    else:
        trimmed = history

    with open(path, "w", encoding="utf-8") as f:
        json.dump(trimmed, f, indent=2, ensure_ascii=False)

    logger.info("Saved %d messages to %s", len(trimmed), path)


def clear_memory(memory_path: str | Path) -> None:
    """Delete the conversation history file.

    Parameters
    ----------
    memory_path : str | Path
        Path to the memory JSON file.
    """
    path = Path(memory_path)
    if path.exists():
        path.unlink()
        logger.info("Cleared memory at %s", path)


def append_exchange(
    history: list[dict],
    question: str,
    answer: str,
) -> list[dict]:
    """Append a user/assistant exchange to the history list.

    Pure function — returns a new list without writing to disk.

    Parameters
    ----------
    history : list[dict]
        Existing history (not mutated).
    question : str
        The user's question.
    answer : str
        The assistant's answer.

    Returns
    -------
    list[dict]
        New history list with the exchange appended.
    """
    return history + [
        {"role": "user", "content": question},
        {"role": "assistant", "content": answer},
    ]
