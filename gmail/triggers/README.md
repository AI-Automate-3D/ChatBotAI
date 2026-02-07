# gmail/triggers/ — Inbox Polling

## poll_inbox.py

Polls Gmail for unread inbox messages and writes them to `trigger_queue.json`.

```bash
# Poll once
python gmail/triggers/poll_inbox.py

# With a query filter
python gmail/triggers/poll_inbox.py --query "from:alice"

# Don't mark as read after queuing
python gmail/triggers/poll_inbox.py --no-mark-read
```

### Trigger queue entry format

```json
{
  "id": "uuid",
  "timestamp": "2025-01-01T00:00:00+00:00",
  "source": "gmail",
  "gmail_message_id": "18f1a2b3c4d5e6f7",
  "gmail_thread_id": "18f1a2b3c4d5e6f7",
  "from": "alice@example.com",
  "to": "me@example.com",
  "subject": "Hello",
  "date": "2025-01-01T00:00:00+00:00",
  "message": {
    "text": "body text",
    "snippet": "short preview",
    "has_attachments": false
  }
}
```
