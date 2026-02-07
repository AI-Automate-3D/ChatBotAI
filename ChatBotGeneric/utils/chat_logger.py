"""JSONL chat logger — appends structured entries to a log file.

Logs every incoming Telegram update as a single JSON line in an
append-only file for audit purposes.

Usage
-----
    from ChatBotGeneric.utils.chat_logger import log_update

    log_update(update)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from telegram import Update

logger = logging.getLogger(__name__)

_BOT_DIR = Path(__file__).resolve().parent.parent
_DEFAULT_LOG_DIR = _BOT_DIR / "log"
_DEFAULT_LOG_FILE = _DEFAULT_LOG_DIR / "chat_log.jsonl"


def log_update(update: Update, log_file: str | Path | None = None) -> dict:
    """Append all available information from a Telegram update to a JSONL file.

    Parameters
    ----------
    update : telegram.Update
        The incoming Telegram update object.
    log_file : str | Path | None
        Path to the JSONL log file.  Defaults to
        ``ChatBotGeneric/log/chat_log.jsonl``.

    Returns
    -------
    dict
        The log entry that was written.
    """
    path = Path(log_file) if log_file else _DEFAULT_LOG_FILE
    path.parent.mkdir(parents=True, exist_ok=True)

    entry = build_log_entry(update)

    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")

    logger.info("Logged update %s to %s", update.update_id, path)
    return entry


def build_log_entry(update: Update) -> dict:
    """Build a structured log entry from a Telegram update.

    Parameters
    ----------
    update : telegram.Update
        The incoming Telegram update object.

    Returns
    -------
    dict
        A dictionary containing timestamp, update_id, message details,
        user metadata, chat metadata, and the raw update dict.
    """
    msg = update.message
    user = update.effective_user
    chat = update.effective_chat

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "update_id": update.update_id,
        "message": {
            "message_id": msg.message_id if msg else None,
            "date": msg.date.isoformat() if msg and msg.date else None,
            "text": msg.text if msg else None,
        },
        "user": {
            "id": user.id if user else None,
            "is_bot": user.is_bot if user else None,
            "first_name": user.first_name if user else None,
            "last_name": user.last_name if user else None,
            "username": user.username if user else None,
        },
        "chat": {
            "id": chat.id if chat else None,
            "type": chat.type if chat else None,
            "title": chat.title if chat else None,
            "username": chat.username if chat else None,
            "first_name": chat.first_name if chat else None,
            "last_name": chat.last_name if chat else None,
        },
        "raw": update.to_dict(),
    }
