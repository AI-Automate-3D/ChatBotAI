# handlers/

Data processing step — reads the trigger queue and builds reply payloads.

## Files

| File | Description |
|------|-------------|
| `build_replies.py` | Reads `trigger_queue.json`, generates a reply for each message, and writes `reply_queue.json`. |
| `reply_queue.json` | JSON array of prepared replies waiting to be sent. Created at runtime, not committed to git. |

## build_replies.py

The central processing step of the pipeline. For each trigger queue entry it:

1. Extracts the chat, user, and message data
2. Calls `generate_reply(text)` to produce a response
3. Wraps everything into a reply queue entry
4. Writes the results to `reply_queue.json`

### Customising Replies

The `generate_reply(text)` function is the plug-in point for your own logic. By default it echoes the message text back. Replace it with your AI agent, lookup table, command parser, etc:

```python
from agent.chat import chat

def generate_reply(text: str) -> str:
    return chat(api_key="...", model="gpt-4.1", ...)
```

### Usage

```bash
# Process all pending triggers
python tg/handlers/build_replies.py

# Filter by chat ID
python tg/handlers/build_replies.py --chat-id 123456789

# Keep trigger queue after processing
python tg/handlers/build_replies.py --no-clear
```

### reply_queue.json Entry Format

```json
{
  "timestamp": "2026-02-07T12:35:00.123+00:00",
  "chat": { "id": 123456789, "type": "private", ... },
  "user": { "id": 987654321, "first_name": "John", ... },
  "original_message": { "message_id": 42, "text": "How do I return an item?", ... },
  "reply": { "text": "How do I return an item?" }
}
```

### Dependencies

- `tg.utils.queue_manager` (shared JSON queue manager)
