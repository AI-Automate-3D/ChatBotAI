"""Send replies via Telegram — takes reply entries directly.

Sends each reply entry to its corresponding chat using the Telegram
Bot API.  Accepts reply entries as function arguments — no file I/O.

Usage
-----
    from tg.actions.send_replies import send_all

    # Send a list of reply entries
    sent_count = await send_all(bot_token, entries)

    # CLI usage
    python tg/actions/send_replies.py --replies '[{"chat":{"id":1},"reply":{"text":"Hi"}}]'
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

from telegram import Bot

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from tg.utils.config import load_config, get_bot_token

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
        Reply entries — each should have ``chat.id`` and ``reply.text``.
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
        description="Send reply entries via Telegram Bot API.",
    )
    parser.add_argument(
        "--replies", "-r",
        type=str,
        default=None,
        help="JSON string of reply entries (list of dicts)",
    )
    parser.add_argument(
        "--chat-id", "-c",
        type=int,
        default=None,
        help="Only send to this chat ID (default: all chats)",
    )
    args = parser.parse_args()

    config = load_config()
    bot_token = get_bot_token(config)

    if not args.replies:
        print(
            "Usage:\n"
            '  python tg/actions/send_replies.py --replies \'[{"chat":{"id":1},"reply":{"text":"Hi"}}]\''
        )
        return

    entries = json.loads(args.replies)
    print(f"Sending {len(entries)} reply(s) ...")

    sent = asyncio.run(send_all(bot_token, entries, filter_chat_id=args.chat_id))
    print(f"Sent {sent} message(s)")


if __name__ == "__main__":
    main()
