# utils/

Shared standalone utilities used across the tg pipeline. Each module can be imported independently into any project.

## Files

| File | Key Functions | Description |
|------|---------------|-------------|
| `config.py` | `load_config()`, `get_bot_token()` | Loads `config.json` and extracts the bot token |
| `chat_logger.py` | `log_update()`, `build_log_entry()` | Appends Telegram updates to a JSONL audit log |
| `queue_manager.py` | `load_queue()`, `save_queue()`, `append_queue()`, `clear_queue()` | JSON file-based queue operations |

## config.py

Loads configuration from `_config files/config.json`. Supports custom paths.

```python
from tg.utils.config import load_config, get_bot_token

config = load_config()                          # default path
config = load_config("/custom/config.json")     # custom path

token = get_bot_token()                         # loads config + extracts token
token = get_bot_token(config)                   # from pre-loaded config
```

## chat_logger.py

Append-only JSONL logging for Telegram updates. Each line is a complete JSON object with timestamp, update_id, message, user, chat, and raw update data.

```python
from tg.utils.chat_logger import log_update

log_update(update)                                      # default log path
log_update(update, log_file="/tmp/my_bot.jsonl")        # custom path
```

Log entries include:
- `timestamp` — ISO 8601 UTC
- `update_id` — unique Telegram update ID
- `message` — message_id, date, text, entities
- `user` — id, name, username, language, premium status
- `chat` — id, type, title, names
- `raw` — complete update dictionary from Telegram

## queue_manager.py

Generic JSON file queue manager. Not Telegram-specific — can be used in any project.

```python
from tg.utils.queue_manager import load_queue, append_queue, save_queue, clear_queue

# Read all entries
entries = load_queue("queue.json")

# Add an entry
append_queue("queue.json", {"key": "value"})

# Overwrite with a new list
save_queue("queue.json", [entry1, entry2])

# Reset to empty
clear_queue("queue.json")
```
