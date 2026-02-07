# gmail/api/ — Standalone Gmail API Functions

Each module wraps a single Gmail API operation. All functions take an authenticated `service` object (from `gmail.utils.auth.get_gmail_service()`) as the first argument.

## Modules

| Module | Function(s) | Description |
|--------|-------------|-------------|
| `get_email.py` | `get_email()` | Fetch a single email by ID |
| `list_emails.py` | `list_emails()`, `search_emails()` | List/search emails with Gmail query syntax |
| `send_email.py` | `send_email()` | Compose and send a new email (with optional attachments) |
| `reply_email.py` | `reply_email()` | Reply to an existing email thread |
| `modify_labels.py` | `mark_read()`, `mark_unread()`, `archive()`, `trash()`, `star()`, `list_labels()` | Modify message labels |
| `get_attachments.py` | `get_attachment()`, `download_all_attachments()` | Download email attachments |

## Usage

```python
from gmail.utils.auth import get_gmail_service
from gmail.api.list_emails import search_emails
from gmail.api.send_email import send_email

service = get_gmail_service()

# Search
emails = search_emails(service, "from:alice subject:meeting")

# Send
send_email(service, to="bob@example.com", subject="Hello", body="Hi Bob!")
```
