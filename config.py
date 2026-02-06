"""Configuration loader for ChatBotAI.

Reads all API keys and settings from a .env file.
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    """Return an env var or exit with a helpful message."""
    value = os.getenv(key)
    if not value:
        sys.exit(f"ERROR: Missing required environment variable: {key}. "
                 f"See .env.example for reference.")
    return value


# Telegram
TELEGRAM_BOT_TOKEN: str = _require("TELEGRAM_BOT_TOKEN")

# OpenAI
OPENAI_API_KEY: str = _require("OPENAI_API_KEY")
OPENAI_CHAT_MODEL: str = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o")
OPENAI_EMBEDDING_MODEL: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

# Pinecone
PINECONE_API_KEY: str = _require("PINECONE_API_KEY")
PINECONE_INDEX_NAME: str = _require("PINECONE_INDEX_NAME")
PINECONE_NAMESPACE: str = os.getenv("PINECONE_NAMESPACE", "chatbot")
PINECONE_CLOUD: str = os.getenv("PINECONE_CLOUD", "aws")
PINECONE_REGION: str = os.getenv("PINECONE_REGION", "us-east-1")

# Google
GOOGLE_SERVICE_ACCOUNT_FILE: str = os.getenv(
    "GOOGLE_SERVICE_ACCOUNT_FILE", "credentials/google-service-account.json"
)

# Agent
AGENT_SYSTEM_PROMPT: str = os.getenv(
    "AGENT_SYSTEM_PROMPT",
    "You are a helpful AI assistant. Use the provided context from the "
    "knowledge base to answer questions accurately. If you don't know the "
    "answer, say so honestly.",
)
AGENT_MAX_HISTORY: int = int(os.getenv("AGENT_MAX_HISTORY", "20"))
