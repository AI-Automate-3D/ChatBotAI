"""Standalone Telegram API — get bot info (getMe).

Wraps the Telegram Bot API ``getMe`` method.  Useful for verifying
that a bot token is valid and retrieving the bot's username, id, etc.

Usage
-----
    from tg.api.get_me import get_me

    info = get_me("BOT_TOKEN")
    print(info["username"])

CLI
---
    python -m tg.api.get_me --token BOT_TOKEN
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging

from telegram import Bot

logger = logging.getLogger(__name__)


async def async_get_me(bot_token: str) -> dict:
    """Retrieve bot information from Telegram (async).

    Parameters
    ----------
    bot_token : str
        Telegram bot API token.

    Returns
    -------
    dict
        Bot info including ``id``, ``is_bot``, ``first_name``,
        ``username``, ``can_join_groups``, etc.
    """
    bot = Bot(token=bot_token)
    me = await bot.get_me()
    logger.info("Bot info: @%s (id=%s)", me.username, me.id)
    return me.to_dict()


def get_me(bot_token: str) -> dict:
    """Retrieve bot information from Telegram (sync wrapper).

    See :func:`async_get_me` for parameter docs.
    """
    return asyncio.run(async_get_me(bot_token=bot_token))


# ── CLI entry point ──────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Get Telegram bot info.")
    parser.add_argument("--token", required=True, help="Bot API token")
    args = parser.parse_args()

    info = get_me(bot_token=args.token)
    print(json.dumps(info, indent=2))


if __name__ == "__main__":
    main()
