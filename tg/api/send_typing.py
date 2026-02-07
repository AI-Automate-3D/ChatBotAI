"""Standalone Telegram API — send a "typing..." chat action.

Wraps the Telegram Bot API ``sendChatAction`` method to show the
typing indicator in a chat.  Can be imported and called from any
project.

Usage
-----
    from tg.api.send_typing import send_typing

    send_typing("BOT_TOKEN", chat_id=123456)

CLI
---
    python -m tg.api.send_typing --token BOT_TOKEN --chat-id 123
"""

from __future__ import annotations

import argparse
import asyncio
import logging

from telegram import Bot
from telegram.constants import ChatAction

logger = logging.getLogger(__name__)


async def async_send_typing(bot_token: str, chat_id: int) -> None:
    """Send a 'typing' chat action to a Telegram chat (async).

    Parameters
    ----------
    bot_token : str
        Telegram bot API token.
    chat_id : int
        Target chat ID.
    """
    bot = Bot(token=bot_token)
    await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    logger.info("Sent typing action to chat %s", chat_id)


def send_typing(bot_token: str, chat_id: int) -> None:
    """Send a 'typing' chat action to a Telegram chat (sync wrapper).

    See :func:`async_send_typing` for parameter docs.
    """
    asyncio.run(async_send_typing(bot_token=bot_token, chat_id=chat_id))


# ── CLI entry point ──────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Send typing indicator.")
    parser.add_argument("--token", required=True, help="Bot API token")
    parser.add_argument("--chat-id", type=int, required=True, help="Target chat ID")
    args = parser.parse_args()

    send_typing(bot_token=args.token, chat_id=args.chat_id)
    print(f"Sent typing indicator to chat {args.chat_id}")


if __name__ == "__main__":
    main()
