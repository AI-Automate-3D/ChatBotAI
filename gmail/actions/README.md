# gmail/actions/ — Reply Sender

## send_replies.py

Reads `reply_queue.json` and sends each reply via the Gmail API. If the entry contains `gmail_message_id` and `gmail_thread_id`, the reply is sent as a threaded reply. Otherwise, it is sent as a new email.

```bash
python gmail/actions/send_replies.py
python gmail/actions/send_replies.py --no-clear
```
