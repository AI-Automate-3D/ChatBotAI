"""Simple conversation memory — per-chat message buffer.

Mirrors the "Simple Memory" node in the workflow diagram.
Stores the last N exchanges (user + assistant) per Telegram chat ID.
"""

from collections import defaultdict, deque

import config


class SimpleMemory:
    """In-memory conversation buffer keyed by chat_id."""

    def __init__(self, max_messages: int = config.AGENT_MAX_HISTORY):
        self._max = max_messages
        self._store: dict[int, deque[dict]] = defaultdict(
            lambda: deque(maxlen=self._max)
        )

    def add_user_message(self, chat_id: int, text: str) -> None:
        self._store[chat_id].append({"role": "user", "content": text})

    def add_assistant_message(self, chat_id: int, text: str) -> None:
        self._store[chat_id].append({"role": "assistant", "content": text})

    def get_history(self, chat_id: int) -> list[dict]:
        """Return the conversation history as a list of message dicts."""
        return list(self._store[chat_id])

    def clear(self, chat_id: int) -> None:
        self._store[chat_id].clear()
