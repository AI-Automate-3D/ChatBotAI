"""Standalone Telegram Bot API wrapper functions.

Each module exposes a single API call that can be imported and used
independently in any project.

    from telegram.api.send_message import send_message
    from telegram.api.send_typing import send_typing
    from telegram.api.get_me import get_me
"""

from telegram.api.send_message import send_message, async_send_message
from telegram.api.send_typing import send_typing, async_send_typing
from telegram.api.get_me import get_me, async_get_me

__all__ = [
    "send_message",
    "async_send_message",
    "send_typing",
    "async_send_typing",
    "get_me",
    "async_get_me",
]
