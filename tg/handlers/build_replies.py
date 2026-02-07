"""Build reply payloads from trigger entries.

Takes a list of trigger entries (incoming messages) and builds a reply
payload for each one.  Returns the replies directly — no file I/O.

The ``generate_reply`` function is a pluggable hook.  Replace it with
your own logic (e.g. call an AI agent) to customise responses.

Usage
-----
    from tg.handlers.build_replies import build_replies, run

    # Direct function call with a list of trigger entries
    replies = build_replies(entries)

    # Or use run() for a single message shortcut
    reply_text = run("Hello, bot!")

    # CLI usage
    python tg/handlers/build_replies.py --message "Hello!"
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

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


def run(text: str) -> str:
    """Generate a reply for a single message string.

    Convenience wrapper that calls ``generate_reply`` directly.

    Parameters
    ----------
    text : str
        The message text.

    Returns
    -------
    str
        The reply text.
    """
    return generate_reply(text)


def build_replies(
    entries: list[dict],
    filter_chat_id: int | None = None,
) -> list[dict]:
    """Build reply queue entries from trigger queue entries.

    Parameters
    ----------
    entries : list[dict]
        Trigger entries — each should have ``chat``, ``user``, and
        ``message`` keys.
    filter_chat_id : int | None
        If set, only process entries from this chat ID.

    Returns
    -------
    list[dict]
        Reply entries ready for sending.
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
            "id": entry.get("id"),
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
    logging.basicConfig(
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        level=logging.INFO,
    )

    parser = argparse.ArgumentParser(
        description="Build reply payloads from trigger entries.",
    )
    parser.add_argument(
        "--trigger", "-t",
        type=str,
        default=None,
        help="JSON string of trigger entries (list of dicts)",
    )
    parser.add_argument(
        "--message", "-m",
        type=str,
        default=None,
        help="Single message text to generate a reply for",
    )
    parser.add_argument(
        "--chat-id", "-c",
        type=int,
        default=None,
        help="Only process messages from this chat ID",
    )
    args = parser.parse_args()

    if args.message:
        reply = run(args.message)
        print(f"Reply: {reply}")
        return

    if args.trigger:
        entries = json.loads(args.trigger)
        replies = build_replies(entries, filter_chat_id=args.chat_id)
        print(json.dumps(replies, indent=2, default=str))
        return

    print(
        "Usage:\n"
        '  python tg/handlers/build_replies.py --message "Hello!"\n'
        '  python tg/handlers/build_replies.py --trigger \'[{"chat":{"id":1},...}]\''
    )


if __name__ == "__main__":
    main()
