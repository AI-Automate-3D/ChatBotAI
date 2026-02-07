"""Telegram Bot trigger — listens for messages and queues them for processing.

A lightweight Telegram bot that listens for incoming text messages,
shows a "typing..." indicator, logs the full update to JSONL, and
appends the message (with chat/user info) to the trigger queue JSON
file so downstream handlers can pick it up.

Usage
-----
    python tg/triggers/bot.py

The bot token is read from config.json under ``telegram.bot_token``.

Data flow
---------
    Telegram user message
        -> log to  tg/log/chat_log.jsonl           (audit trail)
        -> queue in tg/triggers/trigger_queue.json  (for handlers)
"""

from __future__ import annotations

import logging
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ── project imports ───────────────────────────────────────────────────────────

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from tg.utils.config import load_config, get_bot_token
from tg.utils.chat_logger import log_update
from tg.utils.queue_manager import append_queue

# ── paths ─────────────────────────────────────────────────────────────────────

TRIGGER_DIR = Path(__file__).resolve().parent             # tg/triggers/
TG_ROOT = TRIGGER_DIR.parent                               # tg/
TRIGGER_QUEUE = TRIGGER_DIR / "trigger_queue.json"
LAST_CHAT_PATH = TG_ROOT / "last_chat_id.txt"

logger = logging.getLogger(__name__)


# ── handlers ──────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    log_update(update)
    await update.message.reply_text(
        "Hi! Send me a message and I'll pass it along to the system."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming text messages.

    1. Log the full update to JSONL for audit purposes.
    2. Send a 'typing' chat action so the user sees the indicator.
    3. Build a trigger entry and append it to trigger_queue.json.
    4. Save the last chat_id for downstream reply routing.
    5. Acknowledge receipt to the user.
    """
    msg = update.message
    user = update.effective_user
    chat = update.effective_chat

    if not msg or not msg.text:
        return

    logger.info("Message from %s (chat %s): %s", user.first_name, chat.id, msg.text)

    # 1. Audit log (JSONL — never cleared)
    log_update(update)

    # 2. Typing indicator
    await msg.chat.send_action(ChatAction.TYPING)

    # 3. Build trigger entry and queue it
    entry = {
        "id": str(uuid.uuid4()),
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

    append_queue(TRIGGER_QUEUE, entry)
    logger.info("Appended to %s", TRIGGER_QUEUE)

    # 4. Persist last chat_id for reply routing
    LAST_CHAT_PATH.write_text(str(chat.id), encoding="utf-8")

    # 5. Acknowledge
    await msg.reply_text("Got it! Processing your message...")


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    logging.basicConfig(
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        level=logging.INFO,
    )

    config = load_config()
    bot_token = get_bot_token(config)

    logger.info("Starting Telegram bot ...")

    app = ApplicationBuilder().token(bot_token).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run until Ctrl+C
    app.run_polling()


if __name__ == "__main__":
    main()
