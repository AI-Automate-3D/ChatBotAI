"""Telegram ChatBot — main entry point.

Replicates the full n8n workflow:

  Telegram Trigger  ──►  Send Chat Action ("typing")
                    ──►  Get Document (if file attached)
                    ──►  AI Agent - ChatBot
                    ──►  Send Text Message (reply)

Usage:
    1. Copy .env.example to .env and fill in your keys.
    2. pip install -r requirements.txt
    3. python bot.py
"""

import logging

from telegram.ext import ApplicationBuilder

import config
from agent import ChatBotAgent
from services.telegram.handlers import register_handlers

logging.basicConfig(
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Start the Telegram bot (long-polling)."""
    agent = ChatBotAgent()

    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()
    register_handlers(app, agent)

    logger.info("Bot is starting …")
    app.run_polling()


if __name__ == "__main__":
    main()
