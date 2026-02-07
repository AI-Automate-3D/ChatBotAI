"""Standalone JSON queue manager — read, write, append, and clear JSON array files.

Provides a simple file-based queue mechanism using JSON arrays.  Each
queue is a single JSON file containing a list of dictionaries.  This
is the data-passing layer between triggers, handlers, and actions.

Designed to be reusable across projects — no Telegram-specific logic.

Usage
-----
    from telegram.utils.queue_manager import load_queue, append_queue, clear_queue

    # Read all entries
    entries = load_queue("/path/to/queue.json")

    # Add an entry
    append_queue("/path/to/queue.json", {"key": "value"})

    # Clear the queue after processing
    clear_queue("/path/to/queue.json")
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def load_queue(queue_path: str | Path) -> list[dict]:
    """Load all entries from a JSON queue file.

    Parameters
    ----------
    queue_path : str | Path
        Path to the JSON file (a JSON array of objects).

    Returns
    -------
    list[dict]
        The list of entries.  Returns an empty list if the file
        does not exist or is not a valid JSON array.
    """
    path = Path(queue_path)
    if not path.exists():
        return []

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to load queue %s: %s", path, exc)
        return []


def save_queue(queue_path: str | Path, entries: list[dict]) -> None:
    """Overwrite a JSON queue file with the given entries.

    Parameters
    ----------
    queue_path : str | Path
        Path to the JSON file.
    entries : list[dict]
        The full list of entries to write.
    """
    path = Path(queue_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(entries, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    logger.info("Saved %d entries to %s", len(entries), path)


def append_queue(queue_path: str | Path, entry: dict) -> None:
    """Append a single entry to a JSON queue file.

    Creates the file (with a one-element list) if it does not exist.

    Parameters
    ----------
    queue_path : str | Path
        Path to the JSON file.
    entry : dict
        The entry to append.
    """
    entries = load_queue(queue_path)
    entries.append(entry)
    save_queue(queue_path, entries)


def clear_queue(queue_path: str | Path) -> None:
    """Reset a JSON queue file to an empty array.

    Parameters
    ----------
    queue_path : str | Path
        Path to the JSON file.
    """
    path = Path(queue_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("[]", encoding="utf-8")
    logger.info("Cleared queue %s", path)
