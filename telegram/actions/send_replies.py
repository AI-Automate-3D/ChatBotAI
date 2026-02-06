"""Send replies — reads telegram_output.json and sends each reply via Telegram.

Reads the output JSON produced by send_message.py and sends each
reply.text back to its corresponding chat via the Telegram Bot API.

Usage
-----
    # Send all pending replies
    python telegram/actions/send_replies.py

    # Send only to a specific chat
    python telegram/actions/send_replies.py --chat-id 123456789

    # Don't clear the output file after sending
    python telegram/actions/send_replies.py --no-clear
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

from telegram import Bot

# ── paths ────────────────────────────────────────────────────────────────────

ACTIONS_DIR = Path(__file__).resolve().parent        # telegram/actions/
TELEGRAM_ROOT = ACTIONS_DIR.parent                    # telegram/
PROJECT_ROOT = TELEGRAM_ROOT.parent                   # project root
CONFIG_PATH = PROJECT_ROOT / "_config files" / "config.json"
OUTPUT_PATH = TELEGRAM_ROOT / "output" / "telegram_output.json"

logging.basicConfig(
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ── helpers ──────────────────────────────────────────────────────────────────

def load_config() -> dict:
    """Load the full config.json."""
    if not CONFIG_PATH.exists():
        sys.exit(
            f"ERROR: Config file not found: {CONFIG_PATH}\n"
            "Copy config.example.json to config.json and fill in your API keys."
        )
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_output() -> list[dict]:
    """Load pending replies from telegram_output.json."""
    if not OUTPUT_PATH.exists():
        return []
    data = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else []


def clear_output() -> None:
    """Reset telegram_output.json to an empty array."""
    OUTPUT_PATH.write_text("[]", encoding="utf-8")


# ── send ─────────────────────────────────────────────────────────────────────

async def send_all(bot_token: str, entries: list[dict], filter_chat_id: int | None = None) -> int:
    """Send each reply to its chat. Returns count of messages sent."""
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


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Read telegram_output.json and send replies via Telegram.",
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
        help="Don't clear telegram_output.json after sending",
    )
    args = parser.parse_args()

    # Load config
    config = load_config()
    telegram_cfg = config.get("telegram", {})
    bot_token = telegram_cfg.get("bot_token", "")

    if not bot_token:
        sys.exit("ERROR: Missing 'telegram.bot_token' in config.json")

    # Load output
    entries = load_output()
    if not entries:
        print("No pending replies in telegram_output.json")
        return

    print(f"Found {len(entries)} reply(s) in telegram_output.json")

    # Send
    sent = asyncio.run(send_all(bot_token, entries, filter_chat_id=args.chat_id))
    print(f"Sent {sent} message(s)")

    # Clear
    if not args.no_clear:
        clear_output()
        logger.info("Cleared telegram_output.json")


if __name__ == "__main__":
    main()
