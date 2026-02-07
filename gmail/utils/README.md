# gmail/utils/ — Shared Utilities

## Modules

| Module | Description |
|--------|-------------|
| `auth.py` | OAuth2 authentication — `get_gmail_service()`, `authenticate()` |
| `parser.py` | Email content parser — `parse_message()`, `get_header()`, `extract_attachments_metadata()` |
| `queue_manager.py` | JSON queue manager — `load_queue()`, `save_queue()`, `append_queue()`, `clear_queue()` |

## auth.py

Handles the full OAuth2 flow:
1. Loads stored token from `credentials/gmail-token.json`
2. Refreshes if expired
3. Runs the browser consent flow on first use
4. Returns an authenticated `googleapiclient.discovery.Resource`

## parser.py

Converts nested Gmail API message dicts into flat dictionaries with keys like `subject`, `from`, `to`, `body`, `attachments`. Handles multipart MIME, HTML-to-text stripping, and base64 decoding.

## queue_manager.py

Self-contained JSON queue manager (same interface as `tg/utils/queue_manager.py`). Each queue is a JSON file containing an array of dicts.
