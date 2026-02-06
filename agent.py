"""AI Agent — ChatBot.

Mirrors the "AI Agent - ChatBot" node in the workflow diagram.
Combines:
  - services/openai/chat.py         → Chat Model
  - memory.py                       → Simple Memory
  - services/pinecone/vector_store   → Tool (RAG retrieval)
"""

import logging

import config
from memory import SimpleMemory
from services.openai.chat import OpenAIChatModel
from services.pinecone.vector_store import PineconeVectorStore

logger = logging.getLogger(__name__)


class ChatBotAgent:
    """Orchestrates the LLM, memory, and RAG tool for each user turn."""

    def __init__(self) -> None:
        self._chat_model = OpenAIChatModel()
        self._memory = SimpleMemory()
        self._vector_store = PineconeVectorStore()
        self._system_prompt = config.AGENT_SYSTEM_PROMPT

    def handle_message(self, chat_id: int, user_text: str) -> str:
        """Process a user message and return the assistant's reply.

        Steps (matching the workflow):
        1. Retrieve relevant context from Pinecone vector store.
        2. Build the prompt with system message, retrieved context,
           conversation history, and the new user message.
        3. Call the OpenAI chat model.
        4. Store both user and assistant messages in memory.
        5. Return the assistant reply.
        """
        # 1 — RAG retrieval (Pinecone Vector Store tool)
        context = self._vector_store.get_context(user_text)

        # 2 — Build messages
        messages: list[dict] = []

        system_content = self._system_prompt
        if context:
            system_content += (
                "\n\n--- Knowledge Base Context ---\n" + context
            )
        messages.append({"role": "system", "content": system_content})

        # Conversation history from Simple Memory
        messages.extend(self._memory.get_history(chat_id))

        # Current user message
        messages.append({"role": "user", "content": user_text})

        # 3 — Call OpenAI Chat Model
        logger.info("Processing message for chat_id=%s", chat_id)
        reply = self._chat_model.complete(messages)

        # 4 — Persist to memory
        self._memory.add_user_message(chat_id, user_text)
        self._memory.add_assistant_message(chat_id, reply)

        return reply

    def handle_document(self, chat_id: int, document_text: str, caption: str | None = None) -> str:
        """Process a document sent by the user.

        The document text is combined with an optional caption and fed
        through the same agent pipeline.
        """
        prompt = "The user sent a document with the following content:\n\n"
        prompt += document_text
        if caption:
            prompt += f"\n\nUser's message: {caption}"
        else:
            prompt += "\n\nPlease summarize or answer questions about this document."
        return self.handle_message(chat_id, prompt)

    def clear_memory(self, chat_id: int) -> None:
        """Reset conversation memory for a chat."""
        self._memory.clear(chat_id)
