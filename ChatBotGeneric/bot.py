"""Telegram Bot — listens for messages and replies using the AI agent.

A self-contained Telegram bot that receives user messages, passes them
through the RAG agent (Pinecone context + OpenAI), and sends the
answer back.  Logs all updates to JSONL for audit.

Usage
-----
    python ChatBotGeneric/bot.py

The bot token and all API keys are read from ``ChatBotGeneric/config.json``.
"""

from __future__ import annotations

import logging
import sys
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

BOT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BOT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ChatBotGeneric.agent import run, _load_config
from ChatBotGeneric.utils.chat_logger import log_update

logger = logging.getLogger(__name__)


# ── handlers ─────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    log_update(update)
    await update.message.reply_text(
        "Hi! Send me a message and I'll answer using the knowledge base."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming text messages.

    1. Log the full update to JSONL.
    2. Send a 'typing' indicator.
    3. Pass the message through the RAG agent.
    4. Send the agent's answer back to the user.
    """
    msg = update.message
    user = update.effective_user
    chat = update.effective_chat

    if not msg or not msg.text:
        return

    logger.info("Message from %s (chat %s): %s", user.first_name, chat.id, msg.text)

    # Audit log
    log_update(update)

    # Typing indicator
    await msg.chat.send_action(ChatAction.TYPING)

    # Generate reply via agent
    try:
        answer = run(msg.text)
    except Exception as exc:
        logger.error("Agent error: %s", exc)
        answer = "Sorry, something went wrong. Please try again."

    # Send reply
    await msg.reply_text(answer)
    logger.info("Replied to chat %s", chat.id)


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    logging.basicConfig(
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        level=logging.INFO,
    )

    config = _load_config()
    bot_token = config.get("telegram", {}).get("bot_token", "")

    if not bot_token:
        sys.exit("ERROR: Missing 'telegram.bot_token' in config.json")

    logger.info("Starting Telegram bot ...")

    app = ApplicationBuilder().token(bot_token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()


if __name__ == "__main__":
    main()
