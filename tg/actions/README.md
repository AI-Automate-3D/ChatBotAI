# actions/

Action executors — take prepared data and perform external operations.

## Files

| File | Description |
|------|-------------|
| `send_replies.py` | Reads `reply_queue.json` and sends each reply to its chat via the Telegram Bot API. |

## send_replies.py

The final stage of the pipeline. For each reply queue entry it:

1. Extracts the chat ID and reply text
2. Sends the message via `bot.send_message()`
3. Clears `reply_queue.json` after all messages are sent

### Usage

```bash
# Send all pending replies
python tg/actions/send_replies.py

# Send to a specific chat only
python tg/actions/send_replies.py --chat-id 123456789

# Keep reply queue after sending
python tg/actions/send_replies.py --no-clear
```

### Key Function

```python
async def send_all(bot_token: str, entries: list[dict], filter_chat_id: int | None = None) -> int
```

Returns the number of messages successfully sent.

### Dependencies

- `python-telegram-bot`
- `tg.utils.config` (shared config loader)
- `tg.utils.queue_manager` (shared JSON queue manager)
