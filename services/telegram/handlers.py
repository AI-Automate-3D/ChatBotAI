"""Telegram bot handlers.

Mirrors the workflow nodes:
  - Jaded Rose Trigger   (Telegram trigger — incoming messages)
  - Send a chat action   (typing indicator)
  - Get a document       (download file attachments)
  - Send a text message  (reply to user)
"""

import io
import logging

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logger = logging.getLogger(__name__)


def register_handlers(app, agent) -> None:
    """Register all Telegram handlers on *app*."""

    async def start_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(
            "Hello! I'm your AI ChatBot. Send me a message or a document "
            "and I'll do my best to help."
        )

    async def clear_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        agent.clear_memory(update.effective_chat.id)
        await update.message.reply_text("Conversation memory cleared.")

    async def handle_text_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        """Trigger → typing action → AI Agent → reply."""
        chat_id = update.effective_chat.id
        user_text = update.message.text

        # Send chat action (typing indicator)
        await ctx.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

        # AI Agent
        try:
            reply = agent.handle_message(chat_id, user_text)
        except Exception:
            logger.exception("Agent error for chat_id=%s", chat_id)
            reply = "Sorry, something went wrong. Please try again later."

        # Send text message
        await update.message.reply_text(reply)

    async def handle_document(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        """Trigger → typing action → get document → AI Agent → reply."""
        chat_id = update.effective_chat.id

        # Typing indicator
        await ctx.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

        # Get a document
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
                "I can only process text-based documents (txt, csv, json, etc.)."
            )
            return

        caption = update.message.caption

        # AI Agent
        try:
            reply = agent.handle_document(chat_id, document_text, caption)
        except Exception:
            logger.exception("Agent error for chat_id=%s", chat_id)
            reply = "Sorry, something went wrong processing your document."

        # Reply
        await update.message.reply_text(reply)

    # Register
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("clear", clear_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
