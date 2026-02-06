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

import io
import logging

from telegram import Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import config
from agent import ChatBotAgent

logging.basicConfig(
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Shared agent instance
agent = ChatBotAgent()


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

async def start_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start — greet the user."""
    await update.message.reply_text(
        "Hello! I'm your AI ChatBot. Send me a message or a document "
        "and I'll do my best to help."
    )


async def clear_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /clear — reset conversation memory."""
    agent.clear_memory(update.effective_chat.id)
    await update.message.reply_text("Conversation memory cleared.")


async def handle_text_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming text messages.

    Flow:
    1. Send "typing" chat action  (Send a chat action)
    2. Run through AI Agent       (AI Agent - ChatBot)
    3. Reply with result          (Send a text message)
    """
    chat_id = update.effective_chat.id
    user_text = update.message.text

    # Step 1 — Send chat action (typing indicator)
    await ctx.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    # Step 2 — AI Agent processes the message
    try:
        reply = agent.handle_message(chat_id, user_text)
    except Exception:
        logger.exception("Agent error for chat_id=%s", chat_id)
        reply = "Sorry, something went wrong. Please try again later."

    # Step 3 — Send the reply
    await update.message.reply_text(reply)


async def handle_document(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming documents.

    Flow:
    1. Send "typing" chat action   (Send a chat action)
    2. Download & read the document (Get a document)
    3. Run through AI Agent        (AI Agent - ChatBot)
    4. Reply with result           (Send a text message)
    """
    chat_id = update.effective_chat.id

    # Step 1 — Typing indicator
    await ctx.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    # Step 2 — Download the document (Get a document)
    document = update.message.document
    if not document:
        await update.message.reply_text("I couldn't read that document.")
        return

    file = await ctx.bot.get_file(document.file_id)
    buf = io.BytesIO()
    await file.download_to_memory(buf)
    buf.seek(0)

    try:
        document_text = buf.read().decode("utf-8", errors="replace")
    except Exception:
        logger.exception("Failed to read document for chat_id=%s", chat_id)
        await update.message.reply_text(
            "I could only process text-based documents (txt, csv, json, etc.)."
        )
        return

    caption = update.message.caption

    # Step 3 — AI Agent
    try:
        reply = agent.handle_document(chat_id, document_text, caption)
    except Exception:
        logger.exception("Agent error for chat_id=%s", chat_id)
        reply = "Sorry, something went wrong processing your document."

    # Step 4 — Reply
    await update.message.reply_text(reply)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Start the Telegram bot (long-polling)."""
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("clear", clear_command))

    # Messages — text
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

    # Messages — documents
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    logger.info("Bot is starting …")
    app.run_polling()


if __name__ == "__main__":
    main()
