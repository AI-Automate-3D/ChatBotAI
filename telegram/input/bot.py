"""Telegram Bot — receives messages, sends typing action, writes to telegram_input.json.

A lightweight Telegram bot that listens for incoming text messages,
shows a "typing..." indicator, and appends each message (with chat
and user info) to a JSON file so other parts of the system can pick it up.

Usage
-----
    python telegram/input/bot.py

The bot token is read from config.json under "telegram.bot_token".
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ── paths ────────────────────────────────────────────────────────────────────

BOT_DIR = Path(__file__).resolve().parent          # telegram/input/
TELEGRAM_ROOT = BOT_DIR.parent                      # telegram/
PROJECT_ROOT = TELEGRAM_ROOT.parent                  # project root
CONFIG_PATH = PROJECT_ROOT / "_config files" / "config.json"
INPUT_PATH = BOT_DIR / "telegram_input.json"
LOG_DIR = TELEGRAM_ROOT / "log"
LOG_FILE = LOG_DIR / "chat_log.jsonl"

logging.basicConfig(
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ── config ───────────────────────────────────────────────────────────────────

def load_config() -> dict:
    """Load the full config.json from the project root."""
    if not CONFIG_PATH.exists():
        sys.exit(
            f"ERROR: Config file not found: {CONFIG_PATH}\n"
            "Copy config.example.json to config.json and fill in your API keys."
        )
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ── logging ──────────────────────────────────────────────────────────────────

def log_update(update: Update) -> None:
    """Append all available information from an incoming update to chat_log.jsonl."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    msg = update.message
    user = update.effective_user
    chat = update.effective_chat

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "update_id": update.update_id,
        "message": {
            "message_id": msg.message_id if msg else None,
            "date": msg.date.isoformat() if msg and msg.date else None,
            "text": msg.text if msg else None,
            "entities": [
                {
                    "type": e.type,
                    "offset": e.offset,
                    "length": e.length,
                }
                for e in (msg.entities or [])
            ] if msg else [],
        },
        "user": {
            "id": user.id if user else None,
            "is_bot": user.is_bot if user else None,
            "first_name": user.first_name if user else None,
            "last_name": user.last_name if user else None,
            "username": user.username if user else None,
            "language_code": user.language_code if user else None,
            "is_premium": user.is_premium if user else None,
        },
        "chat": {
            "id": chat.id if chat else None,
            "type": chat.type if chat else None,
            "title": chat.title if chat else None,
            "username": chat.username if chat else None,
            "first_name": chat.first_name if chat else None,
            "last_name": chat.last_name if chat else None,
        },
        "raw": update.to_dict(),
    }

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")

    logger.info("Logged update %s to %s", update.update_id, LOG_FILE)


# ── handlers ─────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    log_update(update)
    await update.message.reply_text(
        "Hi! Send me a message and I'll pass it along to the system."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming text messages.

    1. Send a 'typing' chat action so the user sees the indicator.
    2. Append message + chat/user info to telegram_input.json.
    3. Acknowledge receipt.
    """
    msg = update.message
    user = update.effective_user
    chat = update.effective_chat

    logger.info("Message from %s (chat %s): %s", user.first_name, chat.id, msg.text)

    # Log full update data
    log_update(update)

    # Send typing indicator
    await msg.chat.send_action(ChatAction.TYPING)

    # Build input entry with chat and message info
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "chat": {
            "id": chat.id,
            "type": chat.type,
            "title": chat.title,
            "username": chat.username,
            "first_name": chat.first_name,
            "last_name": chat.last_name,
        },
        "user": {
            "id": user.id if user else None,
            "is_bot": user.is_bot if user else None,
            "first_name": user.first_name if user else None,
            "last_name": user.last_name if user else None,
            "username": user.username if user else None,
            "language_code": user.language_code if user else None,
        },
        "message": {
            "message_id": msg.message_id,
            "text": msg.text,
            "date": msg.date.isoformat() if msg.date else None,
        },
    }

    # Append to JSON array file
    _append_input(entry)
    logger.info("Appended to %s", INPUT_PATH)

    # Save last chat_id so the output sender knows where to reply
    LAST_CHAT_PATH = TELEGRAM_ROOT / "last_chat_id.txt"
    LAST_CHAT_PATH.write_text(str(chat.id), encoding="utf-8")

    # Acknowledge
    await msg.reply_text("Got it! Processing your message...")


def _append_input(entry: dict) -> None:
    """Append an entry to telegram_input.json (a JSON array)."""
    if INPUT_PATH.exists():
        data = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    else:
        data = []

    data.append(entry)

    INPUT_PATH.write_text(
        json.dumps(data, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    config = load_config()

    telegram_cfg = config.get("telegram", {})
    bot_token = telegram_cfg.get("bot_token", "")

    if not bot_token:
        sys.exit("ERROR: Missing 'telegram.bot_token' in config.json")

    logger.info("Starting Telegram bot ...")

    app = ApplicationBuilder().token(bot_token).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run until Ctrl+C
    app.run_polling()


if __name__ == "__main__":
    main()
