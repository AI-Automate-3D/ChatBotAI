"""Send replies — reads reply_queue.json and sends each reply via Telegram.

Reads the reply queue produced by ``handlers/build_replies.py`` and
sends each ``reply.text`` back to its corresponding chat using the
Telegram Bot API.

Usage
-----
    # Send all pending replies
    python tg/actions/send_replies.py

    # Send only to a specific chat
    python tg/actions/send_replies.py --chat-id 123456789

    # Don't clear the reply queue after sending
    python tg/actions/send_replies.py --no-clear

Data flow
---------
    tg/handlers/reply_queue.json  (input)
        -> Telegram Bot API  (sends messages)
        -> reply_queue.json cleared
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from telegram import Bot

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from tg.utils.config import load_config, get_bot_token
from tg.utils.queue_manager import load_queue, clear_queue

# ── paths ─────────────────────────────────────────────────────────────────────

ACTIONS_DIR = Path(__file__).resolve().parent               # tg/actions/
TG_ROOT = ACTIONS_DIR.parent                                 # tg/
REPLY_QUEUE = TG_ROOT / "handlers" / "reply_queue.json"

logger = logging.getLogger(__name__)


# ── send ──────────────────────────────────────────────────────────────────────

async def send_all(
    bot_token: str,
    entries: list[dict],
    filter_chat_id: int | None = None,
) -> int:
    """Send each reply entry to its chat via Telegram.

    Parameters
    ----------
    bot_token : str
        Telegram bot API token.
    entries : list[dict]
        Reply queue entries (from reply_queue.json).
    filter_chat_id : int | None
        If set, only send to this chat ID.

    Returns
    -------
    int
        Number of messages successfully sent.
    """
    bot = Bot(token=bot_token)
    sent = 0

    for entry in entries:
        chat_id = entry.get("chat", {}).get("id")
        text = entry.get("reply", {}).get("text")

        if not chat_id or not text:
            logger.warning("Skipping entry — missing chat id or reply text")
            continue

        if filter_chat_id and chat_id != filter_chat_id:
            continue

        await bot.send_message(chat_id=int(chat_id), text=text)
        logger.info("Sent to chat %s: %s", chat_id, text[:80])
        sent += 1

    return sent


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    logging.basicConfig(
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        level=logging.INFO,
    )

    parser = argparse.ArgumentParser(
        description="Read reply_queue.json and send replies via Telegram.",
    )
    parser.add_argument(
        "--chat-id", "-c",
        type=int,
        default=None,
        help="Only send to this chat ID (default: all chats)",
    )
    parser.add_argument(
        "--no-clear",
        action="store_true",
        default=False,
        help="Don't clear reply_queue.json after sending",
    )
    args = parser.parse_args()

    # Load config
    config = load_config()
    bot_token = get_bot_token(config)

    # Load reply queue
    entries = load_queue(REPLY_QUEUE)
    if not entries:
        print("No pending replies in reply_queue.json")
        return

    print(f"Found {len(entries)} reply(s) in reply_queue.json")

    # Send
    sent = asyncio.run(send_all(bot_token, entries, filter_chat_id=args.chat_id))
    print(f"Sent {sent} message(s)")

    # Clear
    if not args.no_clear:
        clear_queue(REPLY_QUEUE)
        logger.info("Cleared reply_queue.json")


if __name__ == "__main__":
    main()
