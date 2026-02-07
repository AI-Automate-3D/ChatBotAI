# triggers/

Event sources that listen for incoming data and queue it for processing.

## Files

| File | Description |
|------|-------------|
| `bot.py` | Telegram bot that listens for messages via polling. Logs every update to `log/chat_log.jsonl` and appends message data to `trigger_queue.json`. |
| `trigger_queue.json` | JSON array of incoming messages waiting to be processed. Created at runtime, not committed to git. |

## bot.py

Runs continuously and listens for Telegram messages. For each incoming message it:

1. Logs the full update to `log/chat_log.jsonl` (append-only audit trail)
2. Sends a typing indicator to the user
3. Builds a trigger entry with chat, user, and message data
4. Appends it to `trigger_queue.json`
5. Saves the chat ID to `last_chat_id.txt`
6. Acknowledges receipt to the user

### Usage

```bash
python tg/triggers/bot.py
```

### trigger_queue.json Entry Format

```json
{
  "timestamp": "2026-02-07T12:34:56.789+00:00",
  "chat": {
    "id": 123456789,
    "type": "private",
    "title": null,
    "username": null,
    "first_name": "John",
    "last_name": "Doe"
  },
  "user": {
    "id": 987654321,
    "is_bot": false,
    "first_name": "John",
    "last_name": "Doe",
    "username": "johndoe",
    "language_code": "en"
  },
  "message": {
    "message_id": 42,
    "text": "How do I return an item?",
    "date": "2026-02-07T12:34:56+00:00"
  }
}
```

### Dependencies

- `python-telegram-bot`
- `tg.utils.config` (shared config loader)
- `tg.utils.chat_logger` (shared JSONL logger)
- `tg.utils.queue_manager` (shared JSON queue manager)
