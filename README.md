# ChatBotAI

A Telegram chatbot powered by OpenAI with RAG (Retrieval-Augmented Generation) via Pinecone and a Google Docs-based knowledge base.

## How It Works

1. A user sends a message to the Telegram bot
2. The bot shows a "typing" indicator
3. The message is used to search a Pinecone vector store for relevant knowledge base context
4. The context, conversation history, and user message are sent to OpenAI (GPT-4o)
5. The AI response is sent back to the user via Telegram

Documents sent to the bot are also processed through the same pipeline.

## Project Structure

```
ChatBotAI/
├── bot.py                          # Entry point — starts the Telegram bot
├── agent.py                        # AI Agent — orchestrates LLM, memory, and RAG
├── memory.py                       # Per-chat conversation memory buffer
├── config.py                       # Loads settings from .env
├── .env.example                    # Config template (copy to .env)
├── requirements.txt
│
├── services/
│   ├── telegram/
│   │   └── handlers.py             # Message trigger, typing action, doc fetch, reply
│   ├── openai/
│   │   ├── chat.py                 # Chat completions (GPT-4o)
│   │   └── embeddings.py           # Text embeddings for vector search
│   ├── google/
│   │   └── docs.py                 # Google Docs fetcher (OAuth2)
│   └── pinecone/
│       ├── vector_store.py         # Vector store retrieval + upsert
│       ├── create_index.py         # Create a new Pinecone index
│       ├── delete_index.py         # Delete a Pinecone index
│       └── update_index.py         # Update/replace vectors in an index
│
└── pinecone_index_updater/
    ├── config.env.example          # Updater config template (copy to config.env)
    ├── parser.py                   # Parses the KB chunk format from Google Docs
    └── updater.py                  # Fetches a Google Doc and syncs to Pinecone
```

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API keys

```bash
cp .env.example .env
```

Edit `.env` and fill in your keys:

| Key | Where to get it |
|-----|----------------|
| `TELEGRAM_BOT_TOKEN` | [BotFather on Telegram](https://t.me/BotFather) |
| `OPENAI_API_KEY` | [OpenAI Platform](https://platform.openai.com/api-keys) |
| `PINECONE_API_KEY` | [Pinecone Console](https://app.pinecone.io/) |
| `PINECONE_INDEX_NAME` | Name of your Pinecone index |
| `GOOGLE_CLIENT_ID` | [Google Cloud Console](https://console.cloud.google.com/apis/credentials) |
| `GOOGLE_CLIENT_SECRET` | Same as above |

### 3. Create the Pinecone index

```bash
python -m services.pinecone.create_index
```

### 4. Populate the knowledge base

Set up the updater config:

```bash
cp pinecone_index_updater/config.env.example pinecone_index_updater/config.env
```

Edit `pinecone_index_updater/config.env` with your Pinecone key, index name, and Google Docs URL, then run:

```bash
python -m pinecone_index_updater.updater
```

On first run, a browser window will open for Google OAuth authorization. The token is saved for future use.

### 5. Start the bot

```bash
python bot.py
```

## Telegram Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Greeting message |
| `/clear` | Reset conversation memory |

## Knowledge Base Format

The Google Doc should use this format:

```
KB_ID: unique_id_here
TYPE: support
TITLE: Entry Title
TEXT:
The content of this knowledge base entry goes here.

--- KB_CHUNK_END ---
```

Each chunk is separated by `--- KB_CHUNK_END ---`. The updater parses these blocks, embeds them via OpenAI, and upserts them into Pinecone.

## Pinecone Management

```bash
# Create a new index
python -m services.pinecone.create_index

# Delete an index
python -m services.pinecone.delete_index

# Show index stats
python -m services.pinecone.update_index --stats

# Upsert vectors from a JSON file
python -m services.pinecone.update_index --file data.json

# Replace all vectors from a JSON file
python -m services.pinecone.update_index --replace data.json --yes

# Delete specific vectors
python -m services.pinecone.update_index --delete-ids vec-1 vec-2

# Sync knowledge base from Google Docs
python -m pinecone_index_updater.updater

# Full replace from Google Docs
python -m pinecone_index_updater.updater --replace
```
