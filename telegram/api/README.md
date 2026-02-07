# api/

Standalone Telegram Bot API wrapper functions. Each file wraps a single API call and can be imported independently into any project.

## Files

| File | Function | Description |
|------|----------|-------------|
| `send_message.py` | `send_message(bot_token, chat_id, text, ...)` | Send a text message to a chat |
| `send_typing.py` | `send_typing(bot_token, chat_id)` | Send a "typing..." indicator |
| `get_me.py` | `get_me(bot_token)` | Get bot info (verify token, get username) |

## Design

Every API function provides:

- **Async version** (`async_send_message`) for use inside event loops
- **Sync version** (`send_message`) that wraps the async version with `asyncio.run()`
- **CLI entry point** for direct execution from the command line

## Usage — as a Library

```python
from telegram.api.send_message import send_message
from telegram.api.send_typing import send_typing
from telegram.api.get_me import get_me

# Send a message
result = send_message("BOT_TOKEN", chat_id=123456, text="Hello!")

# Send typing indicator
send_typing("BOT_TOKEN", chat_id=123456)

# Verify bot token
info = get_me("BOT_TOKEN")
print(info["username"])
```

## Usage — from CLI

```bash
python -m telegram.api.send_message --token BOT_TOKEN --chat-id 123 --text "Hello"
python -m telegram.api.send_typing --token BOT_TOKEN --chat-id 123
python -m telegram.api.get_me --token BOT_TOKEN
```

## send_message.py Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `bot_token` | str | yes | Telegram bot API token |
| `chat_id` | int | yes | Target chat ID |
| `text` | str | yes | Message text |
| `parse_mode` | str | no | `"HTML"`, `"Markdown"`, or `"MarkdownV2"` |
| `disable_notification` | bool | no | Send silently |
| `reply_to_message_id` | int | no | Reply to a specific message |

## Dependencies

- `python-telegram-bot`
