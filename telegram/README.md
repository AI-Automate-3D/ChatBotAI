# Telegram Integration

Receives messages from Telegram, processes them through a pipeline, and sends replies back.

## Architecture

The telegram folder uses a **3-stage pipeline** with JSON files as the data-passing layer between stages:

```
triggers/              ->  handlers/              ->  actions/
(bot listens)              (build replies)            (send replies)
trigger_queue.json         reply_queue.json           Telegram API
```

Each stage runs independently and communicates via JSON queue files. This makes every module reusable in other projects.

## Folders

| Folder | Purpose |
|--------|---------|
| [triggers/](triggers/) | Event sources — bot listener that queues incoming messages |
| [api/](api/) | Standalone Telegram Bot API wrapper functions |
| [handlers/](handlers/) | Data processing — reads trigger queue, builds reply payloads |
| [actions/](actions/) | Action executors — sends queued replies via Telegram |
| [utils/](utils/) | Shared utilities — config, logging, queue management |
| log/ | Append-only JSONL audit trail of all incoming updates |

## Data Flow

```
User sends message on Telegram
    |
    v
triggers/bot.py
    |-- logs to log/chat_log.jsonl (audit, never cleared)
    |-- appends to triggers/trigger_queue.json
    |-- saves chat_id to last_chat_id.txt
    |
    v
handlers/build_replies.py
    |-- reads triggers/trigger_queue.json
    |-- generates reply text (plug in your AI agent here)
    |-- writes handlers/reply_queue.json
    |-- clears trigger_queue.json
    |
    v
actions/send_replies.py
    |-- reads handlers/reply_queue.json
    |-- sends each reply via Telegram Bot API
    |-- clears reply_queue.json
    |
    v
User receives reply on Telegram
```

## Quick Start

```bash
# 1. Start the bot listener (runs continuously)
python telegram/triggers/bot.py

# 2. Process queued messages into replies
python telegram/handlers/build_replies.py

# 3. Send the replies
python telegram/actions/send_replies.py
```

## Configuration

Requires `telegram.bot_token` in `_config files/config.json`:

```json
{
  "telegram": {
    "bot_token": "YOUR_BOT_TOKEN"
  }
}
```

## Using Individual Functions

Every module can be imported standalone:

```python
from telegram.api import send_message, send_typing, get_me
from telegram.utils import load_config, get_bot_token, load_queue, append_queue
```
