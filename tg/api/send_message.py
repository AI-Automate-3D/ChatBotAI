"""Standalone Telegram API — send a text message to a chat.

Wraps the Telegram Bot API ``sendMessage`` method.  Can be imported
and called from any project without pulling in the rest of the
pipeline.

Usage
-----
    from tg.api.send_message import send_message

    # Synchronous wrapper (handles the event loop for you)
    result = send_message("BOT_TOKEN", chat_id=123456, text="Hello!")

    # Async version for use inside an existing event loop
    result = await async_send_message("BOT_TOKEN", chat_id=123456, text="Hello!")

CLI
---
    python -m tg.api.send_message --token BOT_TOKEN --chat-id 123 --text "Hi"
"""

from __future__ import annotations

import argparse
import asyncio
import logging

from telegram import Bot

logger = logging.getLogger(__name__)


async def async_send_message(
    bot_token: str,
    chat_id: int,
    text: str,
    parse_mode: str | None = None,
    disable_notification: bool = False,
    reply_to_message_id: int | None = None,
) -> dict:
    """Send a text message to a Telegram chat (async).

    Parameters
    ----------
    bot_token : str
        Telegram bot API token.
    chat_id : int
        Target chat ID.
    text : str
        Message text to send.
    parse_mode : str | None
        Optional parse mode (``"HTML"``, ``"Markdown"``, ``"MarkdownV2"``).
    disable_notification : bool
        Send silently if True.
    reply_to_message_id : int | None
        If set, the message will be a reply to this message ID.

    Returns
    -------
    dict
        The sent message as a dictionary (from Telegram's response).
    """
    bot = Bot(token=bot_token)
    message = await bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=parse_mode,
        disable_notification=disable_notification,
        reply_to_message_id=reply_to_message_id,
    )
    logger.info("Sent message to chat %s: %s", chat_id, text[:80])
    return message.to_dict()


def send_message(
    bot_token: str,
    chat_id: int,
    text: str,
    parse_mode: str | None = None,
    disable_notification: bool = False,
    reply_to_message_id: int | None = None,
) -> dict:
    """Send a text message to a Telegram chat (sync wrapper).

    See :func:`async_send_message` for parameter docs.
    """
    return asyncio.run(
        async_send_message(
            bot_token=bot_token,
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode,
            disable_notification=disable_notification,
            reply_to_message_id=reply_to_message_id,
        )
    )


# ── CLI entry point ──────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Send a Telegram message.")
    parser.add_argument("--token", required=True, help="Bot API token")
    parser.add_argument("--chat-id", type=int, required=True, help="Target chat ID")
    parser.add_argument("--text", required=True, help="Message text")
    parser.add_argument("--parse-mode", default=None, help="Parse mode (HTML, Markdown, MarkdownV2)")
    args = parser.parse_args()

    result = send_message(
        bot_token=args.token,
        chat_id=args.chat_id,
        text=args.text,
        parse_mode=args.parse_mode,
    )
    print(f"Sent message ID: {result.get('message_id')}")


if __name__ == "__main__":
    main()
