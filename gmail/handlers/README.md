# gmail/handlers/ — Reply Builder

## build_replies.py

Reads `trigger_queue.json`, generates a reply for each email, and writes the results to `reply_queue.json`.

```bash
python gmail/handlers/build_replies.py
python gmail/handlers/build_replies.py --from "alice@example.com"
python gmail/handlers/build_replies.py --no-clear
```

### Customising replies

Replace the `generate_reply(text, subject)` function with your own logic — e.g. call an AI agent, look up a knowledge base, or run a command parser.

### Reply queue entry format

```json
{
  "id": "uuid (from trigger)",
  "timestamp": "2025-01-01T00:00:00+00:00",
  "gmail_message_id": "18f1a2b3c4d5e6f7",
  "gmail_thread_id": "18f1a2b3c4d5e6f7",
  "to": "alice@example.com",
  "subject": "Re: Hello",
  "original_message": { "text": "...", "snippet": "..." },
  "reply": { "text": "reply body" }
}
```
