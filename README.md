# ChatBotAI

A modular toolkit of standalone API functions, processing pipelines, and AI agent components. Each module is independently importable and designed to be composed into agentic workflows.

## Structure

```
ChatBotAI/
├── ChatBotGeneric/ Self-contained Telegram RAG chatbot (start here)
├── tg/             Telegram Bot — API functions & message pipeline
├── gmail/          Gmail — API functions & email pipeline
├── agent/          RAG chatbot — OpenAI + Pinecone retrieval
├── tools/
│   ├── pinecone/   Vector database toolkit & CLI
│   └── openai/     Embedding & knowledge base ingestion
└── _config files/  Configuration templates
```

## Pipelines

Both `tg/` and `gmail/` follow the same 3-stage pipeline pattern with JSON queue files as the data layer:

```
triggers/  →  handlers/  →  actions/
(input)       (process)     (output)
```

| Stage | Telegram | Gmail |
|-------|----------|-------|
| **Triggers** | Bot listener → `trigger_queue.json` | Inbox poller → `trigger_queue.json` |
| **Handlers** | `trigger_queue.json` → `reply_queue.json` | `trigger_queue.json` → `reply_queue.json` |
| **Actions** | `reply_queue.json` → send via Bot API | `reply_queue.json` → send via Gmail API |

Each stage runs independently. Replace `generate_reply()` in any handler to plug in your own logic (AI agent, lookup table, auto-responder, etc.).

## Packages

### ChatBotGeneric/ — Ready-to-Deploy Telegram Chatbot

A self-contained AI chatbot that answers questions from your own documents via Telegram. Powered by RAG (Retrieval-Augmented Generation) with Pinecone vector search and OpenAI. Everything lives in one folder — config, system message, memory, and bot code. Fill in the API keys, start the bot.

```bash
python ChatBotGeneric/bot.py   # Start the Telegram bot
```

```python
from ChatBotGeneric.agent import run
answer = run("What is your returns policy?")
```

See [`ChatBotGeneric/README.md`](ChatBotGeneric/README.md) for full setup and documentation.

### tg/ — Telegram

Standalone API wrappers and a message processing pipeline for Telegram bots.

```python
from tg.api.send_message import send_message
from tg.api.send_typing import send_typing
from tg.api.get_me import get_me
from tg.utils.config import load_config, get_bot_token
from tg.utils.queue_manager import load_queue, append_queue
```

```bash
python tg/triggers/bot.py          # Start bot listener
python tg/handlers/build_replies.py # Process trigger queue
python tg/actions/send_replies.py   # Send replies
```

### gmail/ — Gmail

Standalone Gmail API functions and an email processing pipeline using OAuth2.

```python
from gmail.utils.auth import get_gmail_service
from gmail.api.get_email import get_email
from gmail.api.list_emails import list_emails, search_emails
from gmail.api.send_email import send_email
from gmail.api.reply_email import reply_email
from gmail.api.modify_labels import mark_read, archive, trash, star
from gmail.api.get_attachments import download_all_attachments
```

```bash
python gmail/triggers/poll_inbox.py    # Poll for new emails
python gmail/handlers/build_replies.py # Process trigger queue
python gmail/actions/send_replies.py   # Send replies
```

### agent/ — RAG Chatbot

Retrieval-Augmented Generation chatbot using OpenAI for chat and Pinecone for context retrieval.

```python
from agent.memory import load_memory, save_memory, clear_memory
from agent.context import retrieve_context
from agent.chat import chat, chat_simple
from agent.prompt import load_prompt
```

```bash
python agent/agent.py   # Run the agent
```

### tools/pinecone/ — Vector Database Toolkit

Full-featured Pinecone toolkit — vector operations, embeddings, document parsing (.docx/.txt/.csv), namespace management, and backup/restore.

```python
from tools.pinecone import PineconeConfig, VectorStore
from tools.pinecone.embeddings import make_embed_fn, embed_text, embed_batch
from tools.pinecone.parser import parse_file, parse_docx, parse_txt, parse_csv
from tools.pinecone.fetch import fetch_vectors, fetch_one, vector_exists
from tools.pinecone.namespace_manager import list_namespaces, copy_namespace
from tools.pinecone.backup import export_namespace, import_vectors
```

```bash
python -m tools.pinecone.cli index create --dimension 1536
python -m tools.pinecone.cli vectors query --text "search terms" --top-k 5
python -m tools.pinecone.cli vectors upsert --file data.csv
python -m tools.pinecone.cli namespace list
python -m tools.pinecone.cli backup export --file backup.json
```

### tools/openai/ — Embedding & Ingestion

Parse `.docx` knowledge base documents, embed with OpenAI, and upsert to Pinecone.

```bash
python tools/openai/OpenAI_embeddings.py
```

## Setup

1. Clone the repo and install dependencies:

```bash
pip install python-telegram-bot openai pinecone python-docx
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

2. Copy and fill in your configuration:

```bash
cp "_config files/config.example.json" "_config files/config.json"
cp .env.example .env
```

3. For Gmail — download OAuth2 client secrets from [Google Cloud Console](https://console.cloud.google.com/apis/credentials), enable the Gmail API, and save as `credentials/gmail-credentials.json`. A browser window opens on first run to authorize.

4. For Telegram — create a bot via [@BotFather](https://t.me/BotFather) and add the token to your config.

## Configuration

Settings can be provided via `_config files/config.json` or environment variables (`.env`):

| Service | Config Key | Env Variable |
|---------|-----------|--------------|
| Telegram | `telegram.bot_token` | `TELEGRAM_BOT_TOKEN` |
| OpenAI | `openai.api_key` | `OPENAI_API_KEY` |
| Pinecone | `pinecone.api_key` | `PINECONE_API_KEY` |
| Gmail | `gmail.credentials_file` | `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` |
| Agent | `agent.chat_model` | `OPENAI_CHAT_MODEL` |

See `.env.example` and `_config files/config.example.json` for all available settings.
