# ChatBotGeneric

A ready-to-deploy AI chatbot that connects to Telegram and answers questions using your own knowledge base.

You upload your documents. Your users ask questions on Telegram. The bot reads your knowledge base and gives accurate, sourced answers in seconds — no training, no coding, no machine-learning expertise required.

---

## What Does It Do?

Imagine you have a pile of documents — product manuals, company policies, FAQs, training guides, research notes — and you want people to be able to ask questions and get instant, accurate answers from that material.

That's exactly what this bot does.

1. **You load your documents** into a knowledge base (Pinecone vector store).
2. **You start the Telegram bot** with a single command.
3. **Anyone with the Telegram link** can now ask questions and get answers drawn directly from your documents.

The bot doesn't guess. It doesn't make things up. It searches your knowledge base, finds the most relevant information, and uses AI to write a clear, natural-language answer based on what it found.

---

## Who Is This For?

- **Business owners** who want a 24/7 support bot that actually knows their products
- **Teams** who want an internal assistant that answers from company docs
- **Educators** who want students to query course material
- **Anyone** who has documents and wants a chatbot that answers from them — not from the open internet

---

## How It Works (The Simple Version)

```
User sends a question on Telegram
        |
        v
Bot searches your knowledge base for relevant info
        |
        v
AI reads the relevant info and writes an answer
        |
        v
Answer is sent back to the user on Telegram
```

The bot also remembers recent conversation — so users can ask follow-up questions naturally, just like talking to a person.

---

## How It Works (The Technical Version)

This is a **Retrieval-Augmented Generation (RAG)** chatbot built on a modular Python architecture. Here's what's under the hood:

### RAG Pipeline

RAG is a technique that grounds AI responses in real data rather than relying on the model's general training. The pipeline works in three stages:

1. **Embedding & Retrieval** — When a user asks a question, the bot converts it into a mathematical representation (a vector embedding using OpenAI's `text-embedding-3-small` model) and performs a similarity search against a Pinecone vector database. This finds the most semantically relevant chunks of your documents — even if the user's wording doesn't exactly match the source text.

2. **Context Injection** — The retrieved document chunks are injected into the AI prompt alongside the user's question. This gives the language model the specific information it needs to answer accurately, rather than hallucinating from general knowledge.

3. **Chat Completion** — The full prompt (system instructions + retrieved context + conversation history + user question) is sent to OpenAI's GPT-4.1 model, which generates a natural-language response grounded in your actual documents.

### Vector Search (Pinecone)

Documents are stored as high-dimensional vector embeddings in a Pinecone index. When a question comes in, the bot doesn't do keyword matching — it performs **semantic similarity search**. This means asking "How do I send something back?" will match a document about "Returns Policy" even though the words are completely different. The `top_k` parameter controls how many document chunks are retrieved per query (default: 5).

### Conversation Memory

The bot maintains a local JSON-based conversation history (`memory.json`). The `max_history` config parameter controls how many previous exchanges (question + answer pairs) are included in each API call. This gives the AI context for follow-up questions like "Can you explain that in more detail?" or "What about the second point?" — without re-explaining the topic. Memory auto-trims to prevent token overflow.

### System Message

The bot's personality and behaviour rules are defined in `system_message.txt` — a plain text file you can edit freely. This is the instruction set that tells the AI how to behave: what tone to use, what to do when it doesn't know the answer, and any domain-specific rules. No code changes needed — just edit the text file.

### Telegram Integration

Built on the `python-telegram-bot` library with async message handling. Every incoming message is:
- Logged to a JSONL audit trail (`log/chat_log.jsonl`)
- Passed through the RAG agent pipeline
- Replied inline with the AI-generated answer

The bot shows a typing indicator while processing so users know it's working.

### Architecture

```
ChatBotGeneric/
|
|-- bot.py              Telegram bot — receives messages, replies with answers
|-- agent.py            RAG orchestrator — coordinates the full pipeline
|-- chat.py             OpenAI chat completion wrapper
|-- context.py          Pinecone vector search & context retrieval
|-- memory.py           Conversation history manager (configurable depth)
|-- prompt.py           System message loader
|-- config.json         API keys & settings (all in one place)
|-- system_message.txt  Bot personality & behaviour rules
|-- memory.json         Conversation history (auto-generated at runtime)
|-- utils/
|   |-- chat_logger.py  JSONL audit logger
|-- log/
|   |-- chat_log.jsonl  Full message audit trail (auto-generated)
```

Every module is standalone and independently importable. The agent can be called directly from Python without the Telegram bot — useful for testing, batch processing, or plugging into other interfaces.

---

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Language Model | OpenAI GPT-4.1 | Generates natural-language answers |
| Embeddings | OpenAI text-embedding-3-small | Converts text to vectors for search |
| Vector Database | Pinecone | Stores and searches document embeddings |
| Messaging | Telegram Bot API | User-facing chat interface |
| Runtime | Python 3.10+ | Application logic |

---

## Setup

### 1. Install dependencies

```bash
pip install python-telegram-bot openai pinecone
```

### 2. Get your API keys

| Key | Where to get it |
|-----|----------------|
| OpenAI API key | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| Pinecone API key | [app.pinecone.io](https://app.pinecone.io) |
| Telegram bot token | Message [@BotFather](https://t.me/BotFather) on Telegram |

### 3. Fill in config.json

```bash
cp ChatBotGeneric/config.example.json ChatBotGeneric/config.json
```

Open `ChatBotGeneric/config.json` and add your keys:

```json
{
  "openai": {
    "api_key": "sk-your-openai-key",
    "embedding_model": "text-embedding-3-small",
    "chat_model": "gpt-4.1"
  },
  "pinecone": {
    "api_key": "your-pinecone-key",
    "index_name": "your-index-name",
    "namespace": "your-namespace"
  },
  "telegram": {
    "bot_token": "your-telegram-bot-token"
  },
  "agent": {
    "system_prompt_file": "system_message.txt",
    "top_k": 5,
    "max_history": 10
  }
}
```

### 4. Edit the system message

Open `system_message.txt` and write whatever instructions you want the bot to follow. This controls its tone, rules, and personality.

### 5. Load your documents into Pinecone

Use the included Pinecone toolkit to embed and upload your documents:

```bash
python -m tools.pinecone.cli vectors upsert --file your_data.csv
```

### 6. Start the bot

```bash
python ChatBotGeneric/bot.py
```

The bot is now live on Telegram. Send it a message.

---

## Configuration Reference

| Setting | Location | Default | What it does |
|---------|----------|---------|-------------|
| `openai.api_key` | config.json | `""` | Your OpenAI API key |
| `openai.chat_model` | config.json | `"gpt-4.1"` | Which AI model generates answers |
| `openai.embedding_model` | config.json | `"text-embedding-3-small"` | Which model converts text to vectors |
| `pinecone.api_key` | config.json | `""` | Your Pinecone API key |
| `pinecone.index_name` | config.json | `""` | Name of your Pinecone index |
| `pinecone.namespace` | config.json | `""` | Namespace within the index |
| `telegram.bot_token` | config.json | `""` | Your Telegram bot token |
| `agent.system_prompt_file` | config.json | `"system_message.txt"` | Path to the system message file |
| `agent.top_k` | config.json | `5` | How many document chunks to retrieve per question |
| `agent.max_history` | config.json | `10` | How many past exchanges to remember (set to 0 to disable) |

---

## Using the Agent Without Telegram

The agent works as a standalone Python function:

```python
from ChatBotGeneric.agent import run

answer = run("What is your returns policy?")
print(answer)
```

Or from the command line:

```bash
python ChatBotGeneric/agent.py "What is your returns policy?"
python ChatBotGeneric/agent.py --clear   # Reset conversation memory
```
