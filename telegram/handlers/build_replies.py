"""Build reply payloads — reads trigger_queue.json and writes reply_queue.json.

Reads every entry from the trigger queue, builds a reply payload for
each message, and writes the results to the reply queue.  A separate
action process then picks up the reply queue and sends the messages
via the Telegram API.

Currently echoes the original text back.  Replace the ``generate_reply``
function with your own logic (e.g. call an AI agent) to customise
responses.

Usage
-----
    # Process all pending triggers
    python telegram/handlers/build_replies.py

    # Process only messages from a specific chat
    python telegram/handlers/build_replies.py --chat-id 123456789

    # Don't clear the trigger queue after processing
    python telegram/handlers/build_replies.py --no-clear

Data flow
---------
    telegram/triggers/trigger_queue.json  (input)
        -> telegram/handlers/reply_queue.json  (output)
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from telegram.utils.queue_manager import load_queue, save_queue, clear_queue

# ── paths ─────────────────────────────────────────────────────────────────────

HANDLERS_DIR = Path(__file__).resolve().parent              # telegram/handlers/
TELEGRAM_ROOT = HANDLERS_DIR.parent                          # telegram/
TRIGGER_QUEUE = TELEGRAM_ROOT / "triggers" / "trigger_queue.json"
REPLY_QUEUE = HANDLERS_DIR / "reply_queue.json"

logging.basicConfig(
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ── reply logic ───────────────────────────────────────────────────────────────

def generate_reply(text: str) -> str:
    """Generate a reply for the given message text.

    Override this function to plug in your own response logic
    (e.g. an AI agent, lookup table, command parser, etc.).

    Parameters
    ----------
    text : str
        The original message text from the user.

    Returns
    -------
    str
        The reply text to send back.
    """
    # Default: echo the message back
    return text


def build_replies(
    entries: list[dict],
    filter_chat_id: int | None = None,
) -> list[dict]:
    """Build reply queue entries from trigger queue entries.

    Parameters
    ----------
    entries : list[dict]
        Trigger queue entries (from trigger_queue.json).
    filter_chat_id : int | None
        If set, only process entries from this chat ID.

    Returns
    -------
    list[dict]
        Reply queue entries ready for the actions stage.
    """
    replies = []

    for entry in entries:
        chat = entry.get("chat", {})
        chat_id = chat.get("id")
        user = entry.get("user", {})
        message = entry.get("message", {})
        text = message.get("text")

        if not chat_id or not text:
            logger.warning("Skipping entry — missing chat id or text")
            continue

        if filter_chat_id and chat_id != filter_chat_id:
            continue

        reply_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "chat": chat,
            "user": user,
            "original_message": message,
            "reply": {
                "text": generate_reply(text),
            },
        }
        replies.append(reply_entry)

    return replies


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Read trigger_queue.json and write reply_queue.json.",
    )
    parser.add_argument(
        "--chat-id", "-c",
        type=int,
        default=None,
        help="Only process messages from this chat ID (default: all chats)",
    )
    parser.add_argument(
        "--no-clear",
        action="store_true",
        default=False,
        help="Don't clear trigger_queue.json after processing",
    )
    args = parser.parse_args()

    # Load trigger queue
    entries = load_queue(TRIGGER_QUEUE)
    if not entries:
        print("No pending messages in trigger_queue.json")
        return

    print(f"Found {len(entries)} message(s) in trigger_queue.json")

    # Build replies
    replies = build_replies(entries, filter_chat_id=args.chat_id)
    print(f"Built {len(replies)} reply(s)")

    # Write reply queue
    save_queue(REPLY_QUEUE, replies)
    print(f"Output written to {REPLY_QUEUE}")

    # Clear trigger queue
    if not args.no_clear:
        clear_queue(TRIGGER_QUEUE)
        logger.info("Cleared trigger_queue.json")


if __name__ == "__main__":
    main()
